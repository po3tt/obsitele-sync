from aiogram import types
from aiogram.filters import Command


import os
from pathlib import Path
from datetime import datetime
from aiogram import Router, types
from aiogram.types import InputFile
from aiogram.filters import Command
from aiogram import Bot  # Добавьте этот импорт
import config
import logging
import asyncio
import pyzipper  
from typing import Optional


logger = logging.getLogger(__name__)
backup_router = Router()


async def create_zip_with_password(input_dir: Path, output_zip: Path, password: str):
    """Создает ZIP-архив с полным шифрованием (AES-256)"""
    try:
        with pyzipper.AESZipFile(
            output_zip, 
            'w', 
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
            compresslevel=9,
        ) as zipf:
            zipf.setpassword(password.encode('utf-8'))
            zipf.key_size = 256
            # Включаем шифрование имен файлов и структуры каталогов
            zipf.encrypt_names = True
            
            for root, dirs, files in os.walk(input_dir):
                for file in files:
                    file_path = Path(root) / file
                    # Шифруем пути относительно корневой директории
                    arcname = file_path.relative_to(input_dir).as_posix()
                    zipf.write(file_path, arcname=arcname)
                    
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании архива: {str(e)}")
        return False



async def handle_backup(message: types.Message, bot: Bot):
    try:
        if not os.path.exists(config.OBSIDIAN_PATH):
            await message.answer("❌ Директория для резервного копирования не найдена!")
            return

        if not config.BACKUP_PASSWORD:
            await message.answer("❌ Пароль для архива не установлен в конфиге!")
            return

        # Создаем папку для бэкапов
        backup_dir = Path(config.BACKUP_DIR)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = backup_dir / f"obsidian_backup_{timestamp}.zip"
        
        await message.answer("⏳ Начинаю создание резервной копии... Это может занять некоторое время.")
        
        success = await create_zip_with_password(
            input_dir=Path(config.OBSIDIAN_PATH),
            output_zip=zip_filename, 
            password=config.BACKUP_PASSWORD
        )
        
        if not success:
            await message.answer("❌ Не удалось создать архив!")
            return
            
        await message.answer("✅ Резервная копия успешно создана!")

    except Exception as e:
        logger.error(f"Ошибка в обработчике backup: {str(e)}", exc_info=True)
        await message.answer(f"❌ Произошла ошибка: {str(e)}")


async def auto_save_backups(bot: Bot):
    """Автоматическое создание резервных копий по расписанию"""
    while True:
        try:
            if not config.BACKUP_AUTO_SAVE or config.BACKUP_AUTO_SAVE <= 0:
                await asyncio.sleep(3600)  # Проверяем каждые час, если автосохранение выключено
                continue

            interval = config.BACKUP_AUTO_SAVE * 3600  # Конвертируем часы в секунды
            await asyncio.sleep(interval)

            if not os.path.exists(config.OBSIDIAN_PATH):
                logger.error("Авто-бэкап: директория Obsidian не найдена!")
                continue

            # Создаем имя файла с временем бэкапа
            backup_dir = Path(config.BACKUP_DIR)
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = backup_dir / f"auto_backup_{timestamp}.zip"

            # Создаем архив
            success = await create_zip_with_password(
                input_dir=Path(config.OBSIDIAN_PATH),
                output_zip=zip_filename, 
                password=config.BACKUP_PASSWORD
            )

            # Отправляем уведомление
            if success:
                msg = f"✅ Автоматический бэкап создан: {timestamp}"
                await bot.send_message(config.ADMIN_CHAT_ID, msg)
                logger.info(msg)
                
                # Вызываем очистку после каждого успешного бэкапа
                await cleanup_backups()
            else:
                await bot.send_message(config.ADMIN_CHAT_ID, "❌ Не удалось создать автоматический бэкап!")

        except Exception as e:
            logger.error(f"Ошибка в auto_save_backups: {str(e)}")
            await asyncio.sleep(60)  # Пауза при ошибках

# Модифицируем функцию очистки
async def cleanup_backups():
    try:
        backup_dir = Path(config.BACKUP_DIR)
        now = datetime.now()
        backups = sorted(backup_dir.glob("*.zip"), key=os.path.getmtime)
        
        # Удаление по возрасту
        if hasattr(config, 'BACKUP_MAX_AGE'):
            for file in backups:
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if (now - file_time).days > config.BACKUP_MAX_AGE:
                    file.unlink()
                    
        # Удаление по количеству (если задано)
        if hasattr(config, 'BACKUP_MAX_COUNT'):
            while len(backups) > config.BACKUP_MAX_COUNT:
                oldest = backups.pop(0)
                oldest.unlink()
                
    except Exception as e:
        logger.error(f"Ошибка очистки бэкапов: {str(e)}")

def register_backup_handlers(dp):
    dp.message.register(handle_backup, Command("backup"))



from utils.reminder_utils import ReminderParser

# Добавим в конец файла
async def check_and_notify_reminders(bot: Bot):
    parser = ReminderParser(Path(config.OBSIDIAN_PATH))
    while True:
        try:
            events = parser.check_reminders()
            for event in events:
                await bot.send_message(
                    config.ADMIN_CHAT_ID,
                    f"🔔 Напоминание!\n\n{event}"
                )
            await asyncio.sleep(60)  # Проверка каждую минуту
        except Exception as e:
            logger.error(f"Reminder error: {str(e)}")
            await asyncio.sleep(300)

def register_reminder_handlers(dp):
    dp.startup.register(start_reminder_checker)

async def start_reminder_checker(bot: Bot):
    asyncio.create_task(check_and_notify_reminders(bot))





async def start_handler(message: types.Message):
    await message.answer("📚 Бот для сохранения контента в Obsidian готов к работе!")

def register_base_handlers(dp):
    dp.message.register(start_handler, Command("start"))