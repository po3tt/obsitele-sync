import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import logging
logger = logging.getLogger(__name__)

media_group_data: Dict[str, Dict[str, Any]] = {}

def ensure_dirs_exist(base_path: Path):
    """Создаём все необходимые папки для медиа"""
    required_dirs = ['photos', 'videos', 'files', 'voices']
    for folder in required_dirs:
        dir_path = base_path / folder
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Не удалось создать {dir_path}: {str(e)}")
            raise


async def cleanup_media_groups():
    while True:
        await asyncio.sleep(3600)
        current_time = datetime.now()
        for group_id in list(media_group_data):
            if (current_time - media_group_data[group_id]['timestamp']).total_seconds() > 86400:
                del media_group_data[group_id]
