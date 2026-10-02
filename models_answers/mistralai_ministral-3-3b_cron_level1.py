import re
from datetime import datetime, timedelta
from typing import List

def parse_cron_field(field: str) -> set[int]:
    """Парсит одно поле cron-выражения в множество допустимых значений."""
    if field == '*':
        return set(range(1, 7))  # минута/час/день_недели (для часов и минут)
    elif field == '0':  # для дня месяца и месяца
        return {int(field)}
    elif field.isdigit():
        return {int(field)}

    # Разбиваем на списки и диапазоны
    elements = re.findall(r'(\d+|\d{2})|([0-6]|[1-9]\d?)(?:-[0-5]?\d?)?', field)
    result = set()
    for num, range_str in elements:
        if range_str:  # диапазон
            start, end = map(int, range_str.split('-'))
            result.update(range(start, end + 1))
        else:  # число или список
            num = int(num)
            if ',' in field:
                for n in re.findall(r'\d+', field):
                    result.add(int(n))
    return result

def validate_cron(cron: str) -> None:
    """Проверяет корректность cron-выражения."""
    fields = cron.split()
    if len(fields) != 5:
        raise ValueError("Cron выражение должно содержать ровно 5 полей")

    for i, field in enumerate(fields):
        if i == 0:  # минута
            parsed = parse_cron_field(field)
            if not all(0 <= val <= 59 for val in parsed):
                raise ValueError("Минуты должны быть в диапазоне 0-59")
        elif i == 1:  # час
            parsed = parse_cron_field(field)
            if not all(0 <= val <= 23 for val in parsed):
                raise ValueError("Часы должны быть в диапазоне 0-23")
        elif i == 2:  # день месяца
            parsed = parse_cron_field(field)
            if not all(1 <= val <= 31 for val in parsed):
                raise ValueError("День месяца должен быть в диапазоне 1-31")
        elif i == 3:  # месяц
            parsed = parse_cron_field(field)
            if not all(1 <= val <= 12 for val in parsed):
                raise ValueError("Месяц должен быть в диапазоне 1-12")
        else:  # день недели (0-6)
            parsed = parse_cron_field(field)
            if not all(0 <= val <= 6 for val in parsed):
                raise ValueError("День недели должен быть в диапазоне 0-6")

def next_runs(cron: str, from_time: str, count: int) -> List[str]:
    """Возвращает список следующих моментов запуска cron-выражения."""
    validate_cron(cron)
    fields = cron.split()
    minutes_field, hours_field, day_month_field, month_field, week_day_field = map(parse_cron_field, fields)

    current_time = datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    result = []

    while len(result) < count:
        next_run = current_time
        # Проверяем минуту
        if not any(minute in minutes_field for minute in range(60)):
            next_run += timedelta(minutes=1)
            continue

        # Проверяем час
        if not any(hour in hours_field for hour in range(24)):
            next_run += timedelta(days=7)  # сдвигаем на неделю, если не подходит час
            continue

        # Проверяем день месяца (если поле не '*')
        if day_month_field and not any(day in day_month_field for day in range(1, 32)):
            next_run += timedelta(days=7)  # сдвигаем на неделю
            continue

        # Проверяем месяц (если поле не '*')
        if month_field and not any(month in month_field for month in range(1, 13)):
            next_run += timedelta(days=30)  # максимальный день в месяце + 7 дней запаса
            continue

        # Проверяем день недели (если поле не '*')
        if week_day_field and not any(day % 7 in week_day_field for day in range(14)):
            next_run += timedelta(days=7)  # сдвигаем на неделю
            continue

        # Если все условия выполнены, добавляем в результат
        result.append(next_run.isoformat().replace('+00:00', 'Z').replace('.0', '.000'))

        current_time += timedelta(minutes=1)

    return result[:count]
