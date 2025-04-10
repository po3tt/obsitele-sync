import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from aiogram import Bot
import asyncio
logger = logging.getLogger(__name__)

async def download_file(bot: Bot, file_id: str, destination: Path):
    """Улучшенная загрузка с проверкой размера"""
    try:
        # Создаём папку, если её нет
        destination.parent.mkdir(parents=True, exist_ok=True)
        
        file = await bot.get_file(file_id)
        file_size = file.file_size  # Размер в байтах
        
        # Проверяем размер файла (не более 50MB)
        if file_size > 50 * 1024 * 1024:
            raise ValueError("Файл слишком большой (макс. 50MB)")
        
        await bot.download_file(
            file.file_path,
            destination,
            timeout=60  # Увеличиваем таймаут для больших файлов
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка загрузки: {type(e).__name__}: {str(e)}")
        return False

async def process_media_group(
    media_group_id: str,
    media_dir: Path,
    chat_id: int,
    media_group_data: Dict[str, Any],
    bot: Bot
) -> Optional[Dict[str, Any]]:
    """Обработка медиагруппы с улучшенным логированием"""
    try:
        group = media_group_data.get(media_group_id)
        if not group or group.get('processed'):
            return None

        logger.info(f"Начало обработки группы: {media_group_id}")
        group['processed'] = True
        messages = sorted(group['messages'], key=lambda x: x.message_id)

        media_info = {
            'text': next((msg.caption for msg in messages if msg.caption), ""),
            'photos': [],
            'videos': [],
            'files': [],
            'voices': []
        }

        # Костыль для Windows: создаём все подпапки заранее
        for media_type in ['photos', 'videos', 'files', 'voices']:
            (media_dir / media_type).mkdir(exist_ok=True)

        for msg in messages:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if msg.photo:
                file = msg.photo[-1]
                filename = f"photo_{timestamp}.jpg"
                subfolder = 'photos'
            elif msg.video:
                file = msg.video
                filename = f"video_{timestamp}.mp4"
                subfolder = 'videos'
            elif msg.document:
                file = msg.document
                filename = f"doc_{timestamp}{Path(file.file_name).suffix if file.file_name else '.bin'}"
                subfolder = 'files'
            elif msg.voice:
                file = msg.voice
                filename = f"voice_{timestamp}.ogg"
                subfolder = 'voices'
            else:
                continue

            full_path = media_dir / subfolder / filename
            success = await download_file(bot, file.file_id, full_path)
            
            if success and full_path.exists():
                media_info[subfolder].append(f"{subfolder}/{filename}")
            else:
                logger.warning(f"Не удалось сохранить файл: {filename}")

        return media_info

    except Exception as e:
        logger.error(f"Ошибка обработки группы: {str(e)}")
        return None
