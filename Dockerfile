FROM python:3.11-alpine

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p /obsidian /backups

# Точка монтирования для данных
VOLUME ["/obsidian", "/backups"]

CMD ["python", "main.py"]