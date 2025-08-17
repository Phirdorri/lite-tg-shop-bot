import os
from config import dp, db, bot
from aiogram import types
from aiogram.dispatcher import FSMContext
from functions import get_categories_user, get_subcategories_user, send_good
from markups import menu_mkp, promo_mkp
from payments import check_pay, createPayment, getCoins
from states import NewBuy
import qrcode


# Открыть магазин
@dp.callback_query_handler(text='shop')
@dp.callback_query_handler(text='toshop')
async def toshopcall(call: types.CallbackQuery):
    if db.check_ban(call.from_user.id):
        await call.message.delete()
        await call.message.answer('Выберите категорию:', reply_markup=get_categories_user())


# Выбор категории -> показ подкатегорий
@dp.callback_query_handler(text_contains='usercat_')
async def usercatcall(call: types.CallbackQuery):
    if db.check_ban(call.from_user.id):
        catid = call.data.split('_')[1]
        await call.message.delete()
        await call.message.answer('Выберите подкатегорию:', reply_markup=get_subcategories_user(int(catid)))


# Открыть список товаров в подкатегории
@dp.callback_query_handler(text_contains='usersubcat_', state=NewBuy.Paying)
@dp.callback_query_handler(text_contains='usersubcat_', state=NewBuy.Promo)
@dp.callback_query_handler(text_contains='usersubcat_')
async def usersubcatcall(call: types.CallbackQuery, state: FSMContext):
    if db.check_ban(call.from_user.id):
        try:
            await state.finish()
        except:
            pass
        subcatid = call.data.split('_')[1]
        if len(db.check_goods(int(subcatid))) == 0:
            await call.answer('К сожалению, тут пусто', show_alert=True)
        else:
            await call.message.delete()
            await send_good(0, int(subcatid), call.from_user.id)


# Пагинация назад/вперёд по товарам
@dp.callback_query_handler(text_contains='catback_')
async def catbackcall(call: types.CallbackQuery):
    if db.check_ban(call.from_user.id):
        await call.message.delete()
        subcatid = call.data.split('_')[1]
        step = call.data.split('_')[2]
        await send_good(int(step), int(subcatid), call.from_user.id)


@dp.callback_query_handler(text_contains='catnext_')
async def catnextcall(call: types.CallbackQuery):
    if db.check_ban(call.from_user.id):
        await call.message.delete()
        subcatid = call.data.split('_')[1]
        step = call.data.split('_')[2]
        await send_good(int(step), int(subcatid), call.from_user.id)


# Нажата кнопка "Купить" у конкретного товара
@dp.callback_query_handler(text_contains='buyGood_')
async def buyGood(call: types.CallbackQuery, state: FSMContext):
    if db.check_ban(call.from_user.id):
        await call.message.delete()
        goodId = call.data.split('_')[1]
        subCatId = call.data.split('_')[2]
        goodInfo = db.get_goodinfo(goodId)  # [name, description?, price, ...]
        await NewBuy.Promo.set()
        async with state.proxy() as data:
            data['GoodId'] = {"goodId": goodId, "subCatId": subCatId}
        # Предложим ввести промокод ИЛИ сразу пропустить
        await call.message.answer(
            f'Покупка <b>{goodInfo[0]}</b>\nЦена: <b>{goodInfo[2]}</b> $\n\n'
            f'Введите промокод (если есть) или нажмите "Пропустить":',
            reply_markup=promo_mkp(subCatId)
        )


# Пользователь ввёл промокод (или любой текст на этом шаге)
@dp.message_handler(state=NewBuy.Promo)
async def newBuyPromo(message: types.Message, state: FSMContext):
    promocode = (message.text or '').strip()
    async with state.proxy() as data:
        goodId = data['GoodId']["goodId"]
        subCatId = data['GoodId']["subCatId"]

    # Если пользователь явно ничего не ввёл / ввёл "-"/"нет" — идём без промокода
    if promocode == '' or promocode.lower() in {'-', 'нет', 'no', 'none'}:
        # Покажем явное подтверждение без промокода
        mkp = types.InlineKeyboardMarkup()
        mkp.add(
            types.InlineKeyboardButton('Оформить без промокода', callback_data='skipPromo')
        )
        mkp.add(
            types.InlineKeyboardButton('Отменить покупку', callback_data=f'usersubcat_{subCatId}')
        )
        await message.answer('Продолжить без промокода?', reply_markup=mkp)
        return

    promoInfo = db.get_promo_info(promocode)
    if promoInfo is not None:
        # Промокод валиден
        async with state.proxy() as data:
            data['Promo'] = promocode
        promoPercent = promoInfo[1]
        goodInfo = db.get_goodinfo(goodId)

        mkp = types.InlineKeyboardMarkup()
        mkp.add(types.InlineKeyboardButton('Оформить заказ', callback_data='buyOrder'))
        mkp.add(types.InlineKeyboardButton('Отменить покупку', callback_data=f'usersubcat_{subCatId}'))

        try:
            newPrice = round(float(goodInfo[2]) * ((100 - int(promoPercent)) / 100), 2)
        except Exception:
            newPrice = float(goodInfo[2])

        await message.answer(
            f'Применён промокод <b>{promocode}</b>\n'
            f'Заказ:\n\nТовар: <b>{goodInfo[0]}</b>\n'
            f'Цена: <s>{goodInfo[2]}</s> <b>{newPrice}</b>\n\n'
            f'Хотите оформить заказ?',
            reply_markup=mkp
        )
        await NewBuy.next()  # -> Paying
    else:
        # Неверный промокод — не блокируем покупку!
        mkp = types.InlineKeyboardMarkup()
        mkp.add(types.InlineKeyboardButton('Попробовать ещё раз', callback_data=f'usersubcat_{subCatId}'))
        mkp.add(types.InlineKeyboardButton('Продолжить без промокода', callback_data='skipPromo'))
        await message.answer(
            f'Промокод <b>{promocode}</b> не найден или недействителен.\n'
            f'Вы можете попробовать ещё раз или продолжить без промокода.',
            reply_markup=mkp
        )


# Подтверждение заказа
# 1) buyOrder — после успешного промокода (state = Paying)
# 2) skipPromo — сознательный отказ от промокода (state = Promo)
@dp.callback_query_handler(text='buyOrder', state=NewBuy.Paying)
@dp.callback_query_handler(text='skipPromo', state=NewBuy.Promo)
async def buyOrder(call: types.CallbackQuery, state: FSMContext):
    if db.check_ban(call.from_user.id):
        async with state.proxy() as data:
            goodId = data['GoodId']["goodId"]
            subCatId = data['GoodId']["subCatId"]
        goodInfo = db.get_goodinfo(goodId)

        # Цена с/без промокода
        promocode = None
        newPrice = float(goodInfo[2])
        if call.data == "buyOrder":
            # Путь с промокодом: берём из state, если он там есть
            async with state.proxy() as data:
                promocode = data.get('Promo')  # может не быть — на всякий случай
            if promocode:
                promoInfo = db.get_promo_info(promocode)
                if promoInfo:
                    try:
                        newPrice = round(float(goodInfo[2]) * ((100 - int(promoInfo[1])) / 100), 2)
                    except Exception:
                        newPrice = float(goodInfo[2])

        await call.message.delete()

        # Создаём заказ
        orderId = db.add_order(call.from_user.id, goodId, promocode, newPrice)

        # Выбор монеты
        coins = await getCoins()
        mkp = types.InlineKeyboardMarkup(row_width=4)
        for coin in coins:
            mkp.insert(types.InlineKeyboardButton(coin, callback_data=f'crypto_{coin}_{orderId}_{newPrice}'))

        await call.message.answer('Выберите криптовалюту для оплаты', reply_markup=mkp)
        await state.finish()


# Выбор криптовалюты и выдача реквизитов + QR
@dp.callback_query_handler(text_contains='crypto_')
async def cryptocall(call: types.CallbackQuery):
    await call.message.delete_reply_markup()
    crypto = call.data.split('_')[1]
    orderId = call.data.split('_')[2]
    price = call.data.split('_')[3]

    paym = await createPayment(price, crypto)
    pay_amount = paym['pay_amount']
    pay_adress = paym['pay_address']
    pay_currency = paym['pay_currency']
    pay_id = paym['payment_id']

    mkp = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Проверить оплату', callback_data=f'cryptocheck_{pay_id}_{orderId}_{price}')
    db.upd_payment_link(int(orderId), f'cryptocheck_{pay_id}_{orderId}_{price}')
    mkp.add(btn)

    # QR с адресом
    img = qrcode.make(f'{pay_adress}')
    os.makedirs(f"{os.getcwd()}/files/cryptoQrs", exist_ok=True)
    img.save(f"{os.getcwd()}/files/cryptoQrs/{orderId}.png")
    await bot.send_photo(call.from_user.id, open(f"{os.getcwd()}/files/cryptoQrs/{orderId}.png", 'rb'))

    msgId = await call.message.answer(
        f'Переведите: <code>{pay_amount}</code> {pay_currency}\n'
        f'На кошелёк: <code>{pay_adress}</code>\n\n'
        f'После оплаты не забудьте нажать на «Проверить оплату». '
        f'Транзакция может проходить до 2-х часов',
        reply_markup=mkp
    )
    db.upd_msg_reply_id(orderId, msgId["message_id"])


# Проверка оплаты и выдача товара
@dp.callback_query_handler(text_contains='cryptocheck_')
async def cryptocheckcall(call: types.CallbackQuery):
    reply_markup = call.message.reply_markup
    await call.message.delete_reply_markup()

    pay_id = call.data.split('_')[1]
    orderId = call.data.split('_')[2]
    status = await check_pay(pay_id)
    goodId = db.get_good_for_order(orderId)

    if status in {'confirmed', 'sending', 'finished'}:
        db.pay_order(int(orderId))

        # Промокод мог отсутствовать — защищаемся
        promocode = db.get_promo_from_order(orderId)
        if promocode:
            db.use_promo(promocode)

        # Выдача товара:
        # 1) Обычный кейс: берём экземпляр (файл + описание) и удаляем его
        # 2) Безлимитный цифровой: экземпляров нет — пробуем отдать статический файл/сообщение
        try:
            goodInstance = db.give_good_instance(goodId)  # ожидается (instanceId, filename, description)
        except Exception:
            goodInstance = None

        sent_anything = False

        if goodInstance:
            instanceId = goodInstance[0]
            instanceFileName = goodInstance[1]
            instanceDescription = goodInstance[2] if len(goodInstance) > 2 else ''

            try:
                await bot.send_document(
                    call.from_user.id,
                    open(f'{os.getcwd()}/files/goodsInstancesFiles/{instanceFileName}', 'rb'),
                    caption=instanceDescription
                )
                # Чистим одноразовый файл
                try:
                    os.remove(f'{os.getcwd()}/files/goodsInstancesFiles/{instanceFileName}')
                except FileNotFoundError:
                    pass
                sent_anything = True
            except Exception:
                # если файла нет — попробуем fallback
                sent_anything = False

        if not sent_anything:
            # Fallback для безлимитных цифровых товаров:
            # если ты положишь постоянный файл вида files/unlimited/{goodId}.zip (или pdf, txt и т.п.) — отдадим его.
            static_dir = f"{os.getcwd()}/files/unlimited"
            os.makedirs(static_dir, exist_ok=True)
            # попробуем найти любой файл с префиксом goodId.*
            static_file = None
            if os.path.isdir(static_dir):
                for name in os.listdir(static_dir):
                    if name.startswith(f"{goodId}."):
                        static_file = os.path.join(static_dir, name)
                        break

            if static_file and os.path.isfile(static_file):
                try:
                    await bot.send_document(call.from_user.id, open(static_file, 'rb'),
                                            caption='Спасибо за покупку! Это безлимитный цифровой товар.')
                    sent_anything = True
                except Exception:
                    sent_anything = False

        # Сообщение об успехе
        await call.message.answer(
            'Оплата найдена, заказ оплачен. Ваш товар был отправлен выше',
            reply_markup=menu_mkp()
        )

        # Предложим оставить отзыв
        mkp = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton('Оставить отзыв', callback_data=f'takeotziv_{orderId}')
        mkp.add(btn)
        await call.message.answer('Вы можете оставить отзыв о покупке', reply_markup=mkp)

        # Чистим QR
        try:
            os.remove(f"{os.getcwd()}/files/cryptoQrs/{orderId}.png")
        except FileNotFoundError:
            pass

    else:
        await call.answer('Оплата не найдена, попробуйте через 5 минут', show_alert=True)
        # Вернём кнопки проверки, чтобы пользователь мог нажимать снова
        await call.message.edit_reply_markup(reply_markup)
