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
    good_info = db.get_goodinfo(int(goodid))  
    mkp = types.InlineKeyboardMarkup()  
    btns = [
        types.InlineKeyboardButton('Экземпляры товара', callback_data=f'instances_{goodid}'),
        types.InlineKeyboardButton('Название', callback_data=f'changegoodname_{goodid}'),
        types.InlineKeyboardButton('Описание', callback_data=f'changegooddesc_{goodid}'),
        types.InlineKeyboardButton('Цену', callback_data=f'changegoodprice_{goodid}'),
        types.InlineKeyboardButton('Удалить', callback_data=f'delgood_{goodid}'),
        types.InlineKeyboardButton('Отменить', callback_data='admin'),
    ]  
    for b in btns:  
        mkp.add(b)  
    photo = good_info[3]  
    text = f'Название товара: <code>{good_info[0]}</code>\nОписание товара: <code>{good_info[1]}</code>\nЦена: <code>{good_info[2]}</code>\n'
    if photo and photo != 'None':  
        await bot.send_photo(user_id, open(f'{os.getcwd()}/images/{photo}', 'rb'), caption=text, reply_markup=mkp)  
    else:  
        await bot.send_message(user_id, text, reply_markup=mkp)

async def send_good(step, subcatid, user_id):  
    # изменили: если subcatid == 'none', показываем товары без категории
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
        await bot.send_message(user_id, 'К сожалению, тут пусто', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Вернуться', callback_data='toshop')))  
        return  

    # защита индекса
    step = max(0, min(step, len(goods)-1))  
    g = goods[step]  
    name, description, price, photo, goodid = g[1], g[2], float(g[3]), g[4], g[0]  
    price_str = f'{price:.2f}'  

    mkp = types.InlineKeyboardMarkup()  
    # навигация
    if step > 0:  
        mkp.insert(types.InlineKeyboardButton('⬅', callback_data=f'catback_{subcatid}_{step-1}'))  
    mkp.insert(types.InlineKeyboardButton(f'{step+1}/{len(goods)}', callback_data='none'))  
    if step+1 < len(goods):  
        mkp.insert(types.InlineKeyboardButton('➡', callback_data=f'catnext_{subcatid}_{step+1}'))  

    # Проверяем наличие экземпляров
    has_instances = bool(db.get_good_instances(goodid))  
    btn_back = types.InlineKeyboardButton('Назад', callback_data=f'usercat_{db.get_cat_id_by_good(goodid) or "none"}')  

    if has_instances:  
        has_sold_out = False  
        mkp.add(types.InlineKeyboardButton('Купить', callback_data=f'buyGood_{goodid}_{subcatid or "none"}'))  
    else:  
        has_sold_out = True  
        mkp.add(btn_back)  

    # Показываем сообщение
    sold_text = '\n\nНА ДАННЫЙ МОМЕНТ ТОВАРА НЕТ В НАЛИЧИИ ❗️' if has_sold_out else ''  
    caption = f'<b>Название товара</b>: <code>{name}</code>\n<b>Описание</b>: {description}\n<b>Цена</b>: <code>{price_str}</code> ${sold_text}'  
    if photo and photo != 'None':  
        await bot.send_photo(user_id, open(f'{os.getcwd()}/images/{photo}', 'rb'), caption=caption, reply_markup=mkp)  
    else:  
        await bot.send_message(user_id, caption, reply_markup=mkp)
