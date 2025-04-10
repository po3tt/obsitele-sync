from aiogram import types, Bot
from datetime import datetime
import asyncio
from pathlib import Path
import logging


from utils.media_utils import download_file, process_media_group
from utils.file_utils import ensure_dirs_exist
from utils.note_utils import append_to_note
from config import OBSIDIAN_PATH, OBSIDIAN_SAVE_DIR, OBSIDIAN_SAVE_IMAGE, OBSIDIAN_NAME_MD, OBSIDIAN_FORMAT_DATA

logger = logging.getLogger(__name__)
media_group_data = {}

async def send_progress(bot: Bot, chat_id: int, text: str):
    try:
        await bot.send_message(chat_id, text)
    except Exception as e:
        logger.error(f"Progress message error: {e}")

async def handle_message(message: types.Message, bot: Bot):
    try:
        logger.debug(f"New message received: {message.message_id}")
        
        # Prepare paths
        obsidian_path = Path(OBSIDIAN_PATH)
        media_dir = obsidian_path / Path(OBSIDIAN_SAVE_IMAGE) / OBSIDIAN_SAVE_DIR
        
        try:
            ensure_dirs_exist(media_dir)
            logger.debug(f"Directories verified: {media_dir}")
        except Exception as e:
            await message.answer(f"❌ Ошибка создания папок: {str(e)}")
            raise

        # Create note path
        note_path = obsidian_path / (OBSIDIAN_NAME_MD if OBSIDIAN_NAME_MD 
                      else f"{datetime.now().strftime(OBSIDIAN_FORMAT_DATA)}.md")
        logger.debug(f"Note path: {note_path}")

        # Handle media groups
        if message.media_group_id:
            logger.debug(f"Media group detected: {message.media_group_id}")
            
            if message.media_group_id not in media_group_data:
                media_group_data[message.media_group_id] = {
                    'messages': [],
                    'processed': False
                }
                await send_progress(bot, message.chat.id, "⏳ Обрабатываю альбом...")
            
            media_group_data[message.media_group_id]['messages'].append(message)
            await asyncio.sleep(3)  # Wait for all group messages
            
            if not media_group_data[message.media_group_id]['processed']:
                media_info = await process_media_group(
                    message.media_group_id,
                    media_dir,
                    message.chat.id,
                    media_group_data,
                    bot
                )
                media_group_data[message.media_group_id]['processed'] = True
            else:
                return
        else:
            # Single message processing
            logger.debug("Processing single message")
            media_info = {
                'text': message.caption or message.text or "",
                'photos': [],
                'videos': [],
                'files': [],
                'voices': []
            }
            
            if message.photo:
                # обработка фото
                file = message.photo[-1]
                filename = f"photo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                full_path = media_dir / 'photos' / filename
                await download_file(bot, file.file_id, full_path)
                media_info['photos'].append(f"{filename}")
            
            elif message.voice:
                # обработка голосовых сообщений
                file = message.voice
                filename = f"voice_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ogg"  # Голосовые сообщения в TG всегда в формате OGG
                full_path = media_dir / 'voices' / filename
                
                try:
                    await download_file(bot, file.file_id, full_path)
                    media_info['voices'].append(f"{filename}")
                    logger.info(f"Голосовое сообщение сохранено: {filename}")
                except Exception as e:
                    logger.error(f"Ошибка сохранения голосового сообщения: {str(e)}")
                    await message.answer("⚠️ Не удалось сохранить голосовое сообщение")

            elif message.video:
                file = message.video
                filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                full_path = media_dir / 'videos' / filename
                await download_file(bot, file.file_id, full_path)
                media_info['videos'].append(f"{filename}")
            
            elif message.document:
                file = message.document
                # Сохраняем оригинальное имя файла или создаём своё
                if file.file_name:
                    filename = f"{file.file_name}"
                else:
                    filename = f"file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bin"
                
                full_path = media_dir / 'files' / filename
                
                try:
                    await download_file(bot, file.file_id, full_path)
                    media_info['files'].append(f"{filename}")
                    logger.info(f"Документ сохранён: {filename}")
                except Exception as e:
                    logger.error(f"Ошибка сохранения документа: {str(e)}")
                    await message.answer(f"⚠️ Не удалось сохранить документ: {str(e)}")


        # Save to Obsidian
        if media_info and (media_info['text'] or any(media_info.values())):
            try:
                append_to_note(note_path, message, media_info)
                await message.answer("✅ Успешно сохранено!")
            except Exception as e:
                logger.error(f"Ошибка записи заметки: {str(e)}")
                await message.answer(f"❌ Ошибка записи: {str(e)}")
        else:
            logger.warning("Нет данных для сохранения")
            await message.answer("⚠️ Нет контента для сохранения")

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {str(e)}", exc_info=True)
        await message.answer(f"❌ Критическая ошибка: {str(e)}")


def register_media_handlers(dp):
    dp.message.register(handle_message)
