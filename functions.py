import os  
from config import db, bot  
from aiogram import types

async def anti_flood(message: types.Message, **kwargs):
    """
    Обработчик троттлинга: даёт ответ, если сообщения слишком частые.
    Используется с декоратором @dp.throttled(...) в aiogram v2.
    """
    try:
        await message.answer("Слишком часто! Подождите немного ⏳")
    except Exception:
        pass

def get_faq_admin():  
    faq_list = db.get_all_faq_adm()  
    mkp = types.InlineKeyboardMarkup()  
    for i in faq_list:  
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'changefaq_{i[0]}'))  
    mkp.add(types.InlineKeyboardButton('Новый раздел', callback_data='newfaq'))  
    mkp.add(types.InlineKeyboardButton('Вернуться в админ-панель', callback_data='admin'))  
    return mkp

def get_faq_user():  
    faq_list = db.get_all_faq()  
    mkp = types.InlineKeyboardMarkup()  
    for i in faq_list:  
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'getfaq_{i[0]}'))  
    mkp.add(types.InlineKeyboardButton('Вернуться в меню', callback_data='tomenu'))  
    return mkp

def get_categories_admin():  
    cat_list = db.get_all_cat_adm()  
    mkp = types.InlineKeyboardMarkup()  
    for i in cat_list:
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'admincat_{i[0]}'))
    # ➕ новая кнопка: «товар без категории»
    mkp.add(types.InlineKeyboardButton('➕ Товар без категории', callback_data='addgood_nocat'))
    # старая кнопка
    mkp.add(types.InlineKeyboardButton('➕ Добавить категорию', callback_data='addcat'))  
    mkp.add(types.InlineKeyboardButton(' Вернуться в админ-панель', callback_data='admin'))  
    return mkp

def get_categories_user():  
    cat_list = db.get_all_cat()  
    mkp = types.InlineKeyboardMarkup()  
    for i in cat_list:  
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'usercat_{i[0]}'))  
    # теперь добавляем кнопку для товаров без категории
    mkp.add(types.InlineKeyboardButton('Товары без категории', callback_data='usercat_none'))  
    mkp.add(types.InlineKeyboardButton('Вернуться в меню', callback_data='tomenu'))  
    return mkp

def get_subcategories_admin(cat_id):  
    subcat_list = db.get_subcat_adm(cat_id)  
    mkp = types.InlineKeyboardMarkup()  
    for i in subcat_list:  
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'adminsubcat_{i[0]}_{cat_id}'))  
    mkp.add(types.InlineKeyboardButton('➕ Добавить подкатегорию', callback_data=f'addsubcat_{cat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Изменить название', callback_data=f'changenamecat_{cat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Удалить категорию', callback_data=f'delcat_{cat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Вернуться', callback_data='shopSettings'))  
    return mkp

def get_subcategories_user(cat_id):  
    subcat_list = db.get_subcat(cat_id)  
    mkp = types.InlineKeyboardMarkup()  
    for i in subcat_list:  
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'usersubcat_{i[0]}'))  
    # товары без подкатегории
    mkp.add(types.InlineKeyboardButton('Товары без подкатегории', callback_data=f'usersubcat_none_{cat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Вернуться', callback_data='toshop'))  
    return mkp

def get_goods_admin(subcat_id, cat_id):  
    goods_list = db.get_goods(subcat_id)  
    mkp = types.InlineKeyboardMarkup()  
    for i in goods_list:  
        mkp.add(types.InlineKeyboardButton(i[1], callback_data=f'admingood_{i[0]}'))  
    mkp.add(types.InlineKeyboardButton('➕ Добавить товар', callback_data=f'addgood_{subcat_id}_{cat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Изменить название', callback_data=f'changenamesubcat_{subcat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Удалить подкатегорию', callback_data=f'delsubcat_{subcat_id}'))  
    mkp.add(types.InlineKeyboardButton(' Вернуться', callback_data=f'admincat_{cat_id}'))  
    return mkp

def get_good_instances_admin(goodId):  
    mkp = types.InlineKeyboardMarkup()  
    mkp.add(types.InlineKeyboardButton('➕ Добавить экземпляр', callback_data=f'addinstance_{goodId}'))  
    mkp.add(types.InlineKeyboardButton(' Удалить все экземпляры', callback_data=f'Allinstancesdel_{goodId}'))  
    mkp.add(types.InlineKeyboardButton(' Вернуться', callback_data=f'admingood_{goodId}'))  
    return mkp

async def send_admin_good(goodid, user_id):
    """
    Карточка товара в админке + кнопка «Безлимитный …».
    """
    good_info = db.get_goodinfo(int(goodid))  # ожидаем (name, desc, price, photo, ...)
    is_unlim = db.is_good_unlimited(goodid)

    mkp = types.InlineKeyboardMarkup()
    btn_unlim = types.InlineKeyboardButton(
        f"Безлимитный {'вкл' if is_unlim else 'выкл'}",
        callback_data=f"toggle_unlim_{goodid}"
    )
    btns = [
        types.InlineKeyboardButton('Экземпляры товара', callback_data=f'instances_{goodid}'),
        types.InlineKeyboardButton('Название', callback_data=f'changegoodname_{goodid}'),
        types.InlineKeyboardButton('Описание', callback_data=f'changegooddesc_{goodid}'),
        types.InlineKeyboardButton('Цену', callback_data=f'changegoodprice_{goodid}'),
        types.InlineKeyboardButton('Удалить', callback_data=f'delgood_{goodid}'),
        types.InlineKeyboardButton('Отменить', callback_data='admin'),
    ]
    # ВАЖНО: сначала — кнопка безлимитности
    mkp.add(btn_unlim)
    for b in btns:
        mkp.add(b)

    name, description, price, photo = good_info[0], good_info[1], good_info[2], good_info[3]
    text = (
        f'Название товара: <code>{name}</code>\n'
        f'Описание товара: <code>{description}</code>\n'
        f'Цена: <code>{price}</code>\n'
        f'Безлимитный: <b>{"Да" if is_unlim else "Нет"}</b>'
    )
    if photo and photo != 'None':
        await bot.send_photo(user_id, open(f'{os.getcwd()}/images/{photo}', 'rb'), caption=text, reply_markup=mkp)
    else:
        await bot.send_message(user_id, text, reply_markup=mkp)

async def send_good(step, subcatid, user_id):
    # если subcatid == 'none', показываем товары без категории
    if subcatid == 'none':
        goods = db.get_goods_without_cat()
    elif isinstance(subcatid, str) and subcatid.startswith('none_'):
        # товары без подкатегории внутри категории
        cat_id = int(subcatid.split('_')[1])
        goods = db.get_goods_without_subcat(cat_id)
        subcatid = None
    else:
        goods = db.get_goods_user(subcatid)

    if not goods:
        back_mkp = types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton('Вернуться', callback_data='toshop')
        )
        await bot.send_message(user_id, 'К сожалению, тут пусто', reply_markup=back_mkp)
        return

    # защита индекса
    step = max(0, min(step, len(goods) - 1))
    g = goods[step]
    name, description, price, photo, goodid = g[1], g[2], float(g[3]), g[4], g[0]
    price_str = f'{price:.2f}'

    mkp = types.InlineKeyboardMarkup()

    # навигация
    if step > 0:
        mkp.insert(types.InlineKeyboardButton('⬅', callback_data=f'catback_{subcatid}_{step-1}'))
    mkp.insert(types.InlineKeyboardButton(f'{step+1}/{len(goods)}', callback_data='none'))
    if step + 1 < len(goods):
        mkp.insert(types.InlineKeyboardButton('➡', callback_data=f'catnext_{subcatid}_{step+1}'))

    # логика наличия: либо есть экземпляры, либо товар безлимитный — тогда "Купить" доступна
    try:
        is_unlim = bool(db.is_good_unlimited(int(goodid)))
    except Exception:
        is_unlim = False
    has_instances = bool(db.get_good_instances(goodid))

    btn_back = types.InlineKeyboardButton('Назад', callback_data=f'usercat_{db.get_cat_id_by_good(goodid) or "none"}')

    if is_unlim or has_instances:
        # Товар доступен — показываем "Купить"
        mkp.add(types.InlineKeyboardButton('Купить', callback_data=f'buyGood_{goodid}_{subcatid or "none"}'))
        # (по желанию можно добавить "Назад" вторым рядом)
        # mkp.add(btn_back)
        sold_text = ''
    else:
        # Нет ни экземпляров, ни безлимитности — только "Назад"
        mkp.add(btn_back)
        sold_text = '\n\nНА ДАННЫЙ МОМЕНТ ТОВАРА НЕТ В НАЛИЧИИ ❗️'

    caption = (
        f'<b>Название товара</b>: <code>{name}</code>\n'
        f'<b>Описание</b>: {description}\n'
        f'<b>Цена</b>: <code>{price_str}</code> ${sold_text}'
    )

    if photo and photo != 'None':
        try:
            with open(f'{os.getcwd()}/images/{photo}', 'rb') as f:
                await bot.send_photo(user_id, f, caption=caption, reply_markup=mkp)
        except Exception:
            await bot.send_message(user_id, caption, reply_markup=mkp)
    else:
        await bot.send_message(user_id, caption, reply_markup=mkp)

