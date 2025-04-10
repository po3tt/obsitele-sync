import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from utils.file_utils import cleanup_media_groups
from handlers.media_handler import register_media_handlers
from handlers.base import register_base_handlers
from handlers.base import register_backup_handlers
import logging
from handlers.base import cleanup_backups, auto_save_backups
from handlers.base import register_reminder_handlers

logging.basicConfig(level=logging.DEBUG)



async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    register_backup_handlers(dp)
    register_base_handlers(dp)
    register_media_handlers(dp)
    
    asyncio.create_task(cleanup_backups())
    asyncio.create_task(auto_save_backups(bot)) 
    register_reminder_handlers(dp)
    asyncio.create_task(cleanup_media_groups())
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
