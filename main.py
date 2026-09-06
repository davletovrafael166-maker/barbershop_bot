import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Config
from database import init_db, delete_old_temp_data
from handlers import start, booking, admin
from scheduler import start_scheduler

logging.basicConfig(level=logging.INFO)

async def main():
    init_db()
    delete_old_temp_data()
    
    # Создаем бота с базовыми настройками
    bot = Bot(
        token=Config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher()
    
    dp.include_router(start.router)
    dp.include_router(booking.router)
    dp.include_router(admin.router)
    
    start_scheduler(bot)
    
    print("🤖 Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())