from config import dp, bot
from aiogram import types
import start
import support
import admin
import userfaq
import shop
import usermenu
import review

from aiogram.dispatcher.webhook import get_new_configured_app
from aiohttp import web
import os
import ssl

# 1. Настройки вебхука
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + WEBHOOK_PATH  # Полный URL

# 2. Создаем aiohttp приложение
app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)

async def on_startup(app):
    # 3. Устанавливаем вебхук при запуске
    await bot.set_webhook(
        url=WEBHOOK_URL,
        certificate=open("webhook_cert.pem", "rb") if os.path.exists("webhook_cert.pem") else None
    )
    print(f"Вебхук установлен на {WEBHOOK_URL}")

async def on_shutdown(app):
    # 4. Удаляем вебхук при остановке
    await bot.delete_webhook()
    print("Вебхук удален")

if __name__ == "__main__":
    # 5. Настройка обработчиков запуска/остановки
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    # 6. Запуск сервера
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
