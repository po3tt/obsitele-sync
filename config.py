import os

# токен полученный из BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
#пароль на архив бэкапов
BACKUP_PASSWORD = os.getenv("BACKUP_PASSWORD","")

# место хранения вальта. Пример: /Users/Professional/Obsidian
OBSIDIAN_PATH = os.getenv("OBSIDIAN_PATH","")

# название файла в который будем сохранять заметку. 
# если оставить пустым то заметка будет сохраняться с текущей датой и временем по образцу (ниже)
# указанной в OBSIDIAN_FORMAT_DATA. Пример: notes.md
OBSIDIAN_NAME_MD = os.getenv("OBSIDIAN_NAME_MD","")

# если оставляем пустым OBSIDIAN_NAME_MD надо задать какой формат даты и времени необходим
OBSIDIAN_FORMAT_DATA = os.getenv("OBSIDIAN_FORMAT_DATA",'%d.%m.%Y_%H.%M.%S') 

# в каких файлах из вашего вальта будут извлекаться задачи, указываем через запятую в кавычках
# пример ["1.md","Планы/2.md"]
REMINDER_FILES = ["Планы.md"]

# путь куда сохранять медиа файлы. Пример: Прочее/file
OBSIDIAN_SAVE_IMAGE = os.getenv("OBSIDIAN_SAVE_IMAGE","")

# название папки в которую сохранять медиафайлы, если оставить пустым будут 
# ложиться просто в директорию OBSIDIAN_SAVE_IMAGE (выше) 
# в определенные папки videos, photos, files, voices
OBSIDIAN_SAVE_DIR = os.getenv("OBSIDIAN_SAVE_DIR","media-tg")#

# Папка/путь для хранения бэкапов Пример: /appdata/file/backups
BACKUP_DIR = os.getenv("BACKUP_DIR","")  

# Бэкапы
BACKUP_AUTO_SAVE = int(os.getenv("BACKUP_AUTO_SAVE", 24))   # Периодичность бекапов в часах (0 - отключено)
BACKUP_MAX_AGE = int(os.getenv("BACKUP_MAX_AGE", 7)) # Максимальный возраст файлов в днях
BACKUP_MAX_COUNT = int(os.getenv("BACKUP_MAX_COUNT", 7))   # Максимальное количество хранимых бэкапов
ADMIN_CHAT_ID = 123456789  # ID чата для уведомлений (можно получить в любом боте)