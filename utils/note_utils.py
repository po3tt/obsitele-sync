from pathlib import Path
from aiogram.types import Message
from aiogram import types

def get_forward_source(message: Message) -> str:
    if message.forward_from_chat:
        chat_type = "Канал" if message.forward_from_chat.type == "channel" else "Группа"
        return f"{chat_type}: {message.forward_from_chat.title}"
    elif message.forward_from:
        return f"Пользователь: {message.forward_from.full_name}"
    return "Моя заметка"

def append_to_note(note_path: Path, message: types.Message, media_info: dict):
    try:
        
        note_path.parent.mkdir(exist_ok=True, parents=True)
        source = get_forward_source(message)
        content = f"\n## {message.date.strftime('%d-%m-%Y %H:%M')} | {source}\n"
        
        for media_type in ['photos', 'videos', 'files', 'voices']:
            for item in media_info[media_type]:
                content += f"![[{item}]]\n"

        if media_info['text']:
            content += f"{media_info['text']}\n"
        
        with open(note_path, 'a', encoding='utf-8') as f:
            f.write(content+"\n---\n")
            
    except Exception as e:
        logger.error(f"Note append error: {str(e)}")
        raise