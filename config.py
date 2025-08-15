import os
from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from database import DB

# Получаем токен и ID администратора из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
ADMIN_ID = os.environ.get('ADMIN_ID', '')

# Проверка наличия обязательных переменных
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан в переменных окружения!")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не задан в переменных окружения!")

# Инициализация бота с проверкой токена
try:
    bot = Bot(token=BOT_TOKEN, parse_mode='html')
except Exception as e:
    raise ValueError(f"Ошибка инициализации бота: {str(e)}. Проверьте токен!")

# Настройки администраторов
try:
    admins = [int(ADMIN_ID)]  # Преобразуем ID в число
except ValueError:
    raise TypeError(f"ADMIN_ID должен быть числом! Получено: {ADMIN_ID}")

review_channel_url = ''     # url канала с отзывами
review_channel_id = ''      # id канала с отзывами
admin_ulr = ''              # ссылка на администратора

# Инициализация базы данных
db = DB()            # имя файла базы данных Без параметров

# Инициализация диспетчера
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
