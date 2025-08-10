from config import dp, bot
from aiogram.utils import executor
import start
import support
import admin
import userfaq
import shop
import usermenu
import review

# Добавьте новый код ниже (заменяя старый блок запуска)
from aiogram.dispatcher.webhook import get_new_configured_app
from aiohttp import web
import ssl

async def on_startup(app):
    await bot.set_webhook(
        url="https://ВАШ_СЕРВИС.onrender.com/webhook",
        certificate=open("webhook_cert.pem", "rb") if os.path.exists("webhook_cert.pem") else None
    )

async def on_shutdown(app):
    await bot.delete_webhook()

if __name__ == '__main__':
    # Создаем aiohttp-приложение
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # Подключаем обработчик вебхука
    app = get_new_configured_app(dispatcher=dp, path="/webhook")
    
    # Запускаем сервер
    web.run_app(app, host="0.0.0.0", port=8080)
