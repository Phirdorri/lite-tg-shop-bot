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
import asyncio
import atexit
import ssl
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Настройки вебхука
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL") + WEBHOOK_PATH
PORT = int(os.environ.get("PORT", 8080))

# 2. Создаем aiohttp приложение
app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)

# Обработчик для корневого пути
async def handle_root(request):
    logger.info("GET request to root endpoint")
    return web.Response(text="Bot is active!")

# Обработчик для /webhook
async def handle_webhook(request):
    try:
        update = await request.json()
        await dp.process_update(update)
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return web.Response(status=500, text="Internal Server Error")

async def set_webhook():
    """Установка вебхука с повторными попытками"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await bot.delete_webhook()
            await bot.set_webhook(
                url=WEBHOOK_URL,
                drop_pending_updates=True
            )
            logger.info(f"✅ Вебхук установлен на {WEBHOOK_URL}")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка установки вебхука (попытка {attempt+1}/{max_retries}): {e}")
            await asyncio.sleep(5)
    return False

async def on_startup(app):
    """Действия при запуске сервера"""
    logger.info("Запуск сервера...")
    await set_webhook()
    
    # Периодическая проверка вебхука
    asyncio.create_task(webhook_checker())

async def webhook_checker():
    """Периодическая проверка статуса вебхука"""
    while True:
        try:
            webhook_info = await bot.get_webhook_info()
            if not webhook_info.url or WEBHOOK_URL not in webhook_info.url:
                logger.warning("⚠️ Вебхук сброшен! Переустанавливаю...")
                await set_webhook()
        except Exception as e:
            logger.error(f"❌ Ошибка проверки вебхука: {e}")
        
        await asyncio.sleep(300)  # Проверка каждые 5 минут

async def on_shutdown(app):
    """Действия при остановке сервера"""
    logger.info("Остановка сервера...")
    try:
        await bot.delete_webhook()
        logger.info("✅ Вебхук удален")
    except Exception as e:
        logger.error(f"❌ Ошибка удаления вебхука: {e}")
    
    # Закрываем все соединения
    await dp.storage.close()
    await dp.storage.wait_closed()
    await bot.session.close()

# Регистрируем обработчики
app.router.add_get('/', handle_root)
app.router.add_post('/webhook', handle_webhook)

# Регистрируем обработчики событий
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Основная функция
async def main():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    logger.info(f"🚀 Сервер запущен на порту {PORT}")
    
    # Бесконечное ожидание
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    # Регистрируем обработчик Ctrl+C
    atexit.register(lambda: asyncio.run(on_shutdown(app)))
    
    # Запускаем основную корутину
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Приложение остановлено пользователем")
    finally:
        loop.run_until_complete(on_shutdown(app))
        loop.close()
