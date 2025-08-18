from aiogram import types
from config import db

def rules_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Принять', callback_data='rulesok')
    mkp.add(btn1)
    return mkp

def menu_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Магазин', callback_data='shop')
    btn2 = types.InlineKeyboardButton('Мои покупки', callback_data='myPurchs')
    btn3 = types.InlineKeyboardButton('F.A.Q.', callback_data='faq')
    btn4 = types.InlineKeyboardButton('Отзывы', callback_data='reviews')
    btn5 = types.InlineKeyboardButton('Поддержка', callback_data='support')
    mkp.add(btn1, btn2).add(btn3, btn4).add(btn5)
    return mkp

def cancel_mkp(user_id):
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Отменить', callback_data='cancel')
    mkp.add(btn1)
    return mkp

def cancel_adm_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Отменить', callback_data='cancel')
    mkp.add(btn1)
    return mkp

def promo_admin_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Отменить', callback_data='promoSettings')
    mkp.add(btn1)
    return mkp

def menu_back_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Вернуться в меню', callback_data='menu')
    mkp.add(btn1)
    return mkp

def promo_mkp(subCatId):
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Пропустить', callback_data='skipPromo')
    btn2 = types.InlineKeyboardButton('Отменить покупку', callback_data=f'usersubcat_{subCatId}')
    mkp.add(btn1).add(btn2)
    return mkp

def admin_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Настройка товаров', callback_data='shopSettings')
    btn2 = types.InlineKeyboardButton('Пользователи', callback_data='users')
    btn3 = types.InlineKeyboardButton('Промокоды', callback_data='promoSettings')
    btn4 = types.InlineKeyboardButton('Настройки бота', callback_data='settings')
    btn5 = types.InlineKeyboardButton('Режим покупателя', callback_data='menu')
    mkp.add(btn1, btn2).add(btn3, btn4).add(btn5)
    return mkp

def promocodes():
    mkp = types.InlineKeyboardMarkup()
    promos = db.get_promos()
    if promos != None:
        for i in promos:
            mkp.add(types.InlineKeyboardButton(f'{i[1]} - {i[2]}% ({i[3]}/{i[4]})', callback_data=f'promo_{i[0]}'))
    mkp.add(types.InlineKeyboardButton(f'[ Добавить промокод ]', callback_data=f'addpromo'))
    mkp.add(types.InlineKeyboardButton(f'Назад', callback_data=f'admin'))
    return mkp

def del_promo(promoId):
    mkp = types.InlineKeyboardMarkup()
    mkp.add(types.InlineKeyboardButton(f'Удалить промокод?', callback_data=f'promodel_{db.get_promo_info_by_id(promoId)[0]}'))
    mkp.add(types.InlineKeyboardButton(f'Назад', callback_data=f'promoSettings'))
    return mkp

def botsettings_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('Поменять токен Nowpayments', callback_data=f'changeToken')
    btn2 = types.InlineKeyboardButton('Настройка F.A.Q', callback_data=f'faqSettings')
    btn3 = types.InlineKeyboardButton('Изменить правила', callback_data=f'changeRules')
    btn4 = types.InlineKeyboardButton('Назад в админку', callback_data=f'admin')
    mkp.add(btn1).add(btn2).add(btn3).add(btn4)
    return mkp

def all_users_mkp(page):
    users_list = db.get_all_users()
    mkp = types.InlineKeyboardMarkup(row_width=2)
    if page == 1:
        if len(users_list) < 11:
            for i in users_list:
                try:
                    mkp.add(types.InlineKeyboardButton(f'Пользователь {i[1]} | {db.get_usernamerev(int(i[1]))}', callback_data=f'getuser_{i[1]}_{page}'))
                except Exception as ex:
                    print(ex)
        else:
            try:
                for i in range(page-1, page*10):
                    mkp.add(types.InlineKeyboardButton(f'Пользователь {users_list[i][1]} | {db.get_usernamerev(int(users_list[i][1]))}', callback_data=f'getuser_{users_list[i][1]}_{page}'))
                mkp.add(types.InlineKeyboardButton('Далее', callback_data=f'userspage_{page+1}'))
            except:
                pass
    else:
        try:
            for i in range((page-1)*10, page*10):
                mkp.add(types.InlineKeyboardButton(f'Пользователь {users_list[i][1]} | {db.get_usernamerev(int(users_list[i][1]))}', callback_data=f'getuser_{users_list[i][1]}_{page}'))
            mkp.add(types.InlineKeyboardButton('Назад', callback_data=f'userspage_{page-1}'),
                    types.InlineKeyboardButton('Далее', callback_data=f'userspage_{page+1}'))
        except:
            mkp.add(types.InlineKeyboardButton('Назад', callback_data=f'userspage_{page-1}'))
    mkp.add(types.InlineKeyboardButton('Отменить', callback_data='admin'))
    return mkp

# Новый блок: кнопки для функций "Пропустить категорию" и "Безлимитный цифровой"
def skip_category_mkp():
    mkp = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton('Пропустить категорию', callback_data='addgood_skipcat')
    mkp.add(btn)
    return mkp

def unlimited_flag_mkp(subcatid=None, catid=None):
    mkp = types.InlineKeyboardMarkup()
    mkp.add(types.InlineKeyboardButton('Безлимитный цифровой', callback_data='flag_unlimited'))
    mkp.add(types.InlineKeyboardButton('Пропустить фото', callback_data='skip_photo'))
    if subcatid is not None and catid is not None:
        mkp.add(types.InlineKeyboardButton('Отменить', callback_data=f'adminsubcat_{subcatid}_{catid}'))
    return mkp

# --- ↓↓↓ ДОБАВЛЕНО: сервисные клавиатуры для простого товара ↓↓↓
from aiogram import types

def skip_photo_mkp():
    """
    Клавиатура для шага с фото товара: позволяет пропустить фото.
    """
    mkp = types.InlineKeyboardMarkup()
    mkp.add(types.InlineKeyboardButton('📎 Пропустить фото', callback_data='skip_photo'))
    return mkp

def unlimited_flag_mkp(current_on: bool = False, good_id: int = None):
    """
    Универсальная клавиатура «Безлимитный».
    Если good_id указан — используется в карточке товара (переключатель toggle_unlim_<id>).
    Если good_id не указан — может использоваться в мастере создания (unlim_on/unlim_off).
    Сейчас мы используем вариант с good_id (переключатель в карточке товара).
    """
    if good_id is not None:
        text = '✅ Безлимитный: Вкл' if current_on else '❌ Безлимитный: Выкл'
        cb = f'toggle_unlim_{good_id}'
        mkp = types.InlineKeyboardMarkup()
        mkp.add(types.InlineKeyboardButton(text, callback_data=cb))
        return mkp
    else:
        # Резерв на будущее (если захочешь спрашивать флаг прямо в мастере создания)
        mkp = types.InlineKeyboardMarkup()
        if current_on:
            mkp.add(types.InlineKeyboardButton('❌ Безлимитный: Выкл', callback_data='unlim_off'))
        else:
            mkp.add(types.InlineKeyboardButton('✅ Безлимитный: Вкл', callback_data='unlim_on'))
        return mkp
# --- ↑↑↑ ДОБАВЛЕНО ↑↑↑
