import re
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import List, Tuple, Optional
import config
logger = logging.getLogger(__name__)

class ReminderParser:
    def __init__(self, obsidian_path: Path):
        self.obsidian_path = obsidian_path
        self.sent_reminders = set()
        self.day_map = {
            'пн': 0, 'вт': 1, 'ср': 2, 
            'чт': 3, 'пт': 4, 'сб': 5, 'вс': 6
        }

    def parse_line(self, line: str) -> List[Tuple[datetime, str]]:
        patterns = [
            # Формат: [описание задачи] |- дд.мм[.гггг] чч:мм
            (r'^(.+?)\s*\|-\s*(\d{1,2}\.\d{1,2}(?:\.\d{4})?)\s+(\d{1,2}:\d{2})\s*$', self._parse_date_time),
            
            # Формат: [описание задачи] |- пн-вс чч:мм
            (r'^(.+?)\s*\|-\s*(пн|вт|ср|чт|пт|сб|вс)\s+(\d{1,2}:\d{2})\s*$', self._parse_week_day),
            
            # Формат: [описание задачи] |- чч:мм
            (r'^(.+?)\s*\|-\s*(\d{1,2}:\d{2})\s*$', self._parse_time_only)
        ]

        line = line.strip()
        if not line:
            return []

        for pattern, handler in patterns:
            match = re.match(pattern, line)
            if match:
                return handler(match.groups())
                
        return []

    def _parse_date_time(self, groups: tuple) -> List[Tuple[datetime, str]]:
        task, date_str, time_str = groups
        now = datetime.now()
        
        try:
            # Парсим дату
            date_parts = date_str.split('.')
            day = int(date_parts[0])
            month = int(date_parts[1])
            year = int(date_parts[2]) if len(date_parts) > 2 else now.year

            # Парсим время
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            
            # Создаем объект datetime
            reminder_date = datetime(year, month, day, time_obj.hour, time_obj.minute)
            
            # Корректировка даты если она в прошлом
            if reminder_date < now and len(date_parts) == 2:
                reminder_date = reminder_date.replace(year=reminder_date.year + 1)
                
            return [(reminder_date, task.strip())]
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга даты: {str(e)}")
            return []

    def _parse_week_day(self, groups: tuple) -> List[Tuple[datetime, str]]:
        task, day_str, time_str = groups
        now = datetime.now()
        
        try:
            # Парсим день недели и время
            target_day = self.day_map[day_str.lower()]
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            
            # Рассчитываем дату
            current_weekday = now.weekday()
            days_ahead = (target_day - current_weekday) % 7
            if days_ahead == 0 and now.time() > time_obj:
                days_ahead = 7
                
            reminder_date = datetime.combine(
                now.date() + timedelta(days=days_ahead),
                time_obj
            )
            
            return [(reminder_date, task.strip())]
            
        except KeyError:
            logger.warning(f"Неверный день недели: {day_str}")
        except Exception as e:
            logger.warning(f"Ошибка парсинга дня недели: {str(e)}")
            
        return []

    def _parse_time_only(self, groups: tuple) -> List[Tuple[datetime, str]]:
        task, time_str = groups
        now = datetime.now()
        
        try:
            # Парсим время
            time_obj = datetime.strptime(time_str, "%H:%M").time()
            reminder_date = datetime.combine(now.date(), time_obj)
            
            # Корректируем если время прошло
            if reminder_date < now:
                reminder_date += timedelta(days=1)
                
            return [(reminder_date, task.strip())]
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга времени: {str(e)}")
            return []

    def check_reminders(self) -> List[str]:
        events = []
        current_time = datetime.now()
        
        for file_name in config.REMINDER_FILES:
            
            file_path = self.obsidian_path / file_name.strip()
            print (file_path)
            if not self._process_file(file_path, current_time, events):
                continue
                
        self._cleanup_old_reminders(current_time)
        return events

    def _process_file(self, file_path: Path, current_time: datetime, events: list) -> bool:
        if not file_path.exists():
            logger.warning(f"Файл {file_path.name} не найден")
            return False
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    self._process_line(line, line_num, current_time, events, file_path) 
            return True
        except Exception as e:
            logger.error(f"Ошибка чтения файла {file_path.name}: {str(e)}")
            return False

    def _process_line(self, line: str, line_num: int, current_time: datetime, events: list, file_path: Path):
        line = line.strip()
        if not line or '|-' not in line:
            return
            
        try:
            for reminder_time, task in self.parse_line(line):
                time_diff = (reminder_time - current_time).total_seconds()
                identifier = f"{file_path.name}:{reminder_time.timestamp()}:{task}"
                
                if 0 <= time_diff <= 60 and identifier not in self.sent_reminders:
                    events.append(f"⏰ {task} ({reminder_time.strftime('%d.%m.%Y %H:%M')})")
                    self.sent_reminders.add(identifier)
                    
        except Exception as e:
            logger.error(f"Ошибка в строке {line_num}: '{line}'\n{str(e)}")

    def _cleanup_old_reminders(self, current_time: datetime):
        threshold = current_time - timedelta(hours=24)
        new_sent_reminders = set()
        
        for ident in self.sent_reminders:
            try:
                parts = ident.split(':', 2)  # Разделяем только первые два двоеточия
                timestamp_str = parts[1]
                reminder_time = datetime.fromtimestamp(float(timestamp_str))
                if reminder_time > threshold:
                    new_sent_reminders.add(ident)
            except Exception as e:
                logger.warning(f"Ошибка очистки напоминания {ident}: {str(e)}")
        
        self.sent_reminders = new_sent_reminders