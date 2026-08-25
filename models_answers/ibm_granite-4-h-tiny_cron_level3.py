import datetime

def parse_cron(cron):
    parts = cron.split()
    if len(parts) != 5:
        raise ValueError("Invalid cron expression")
    
    minute, hour, day_of_month, month, day_of_week = map(lambda x: x.strip(), parts)
    
    macros = {
        '@hourly': '0 * * * *',
        '@daily': '0 0 * * *',
        '@midnight': '0 0 * * *',
        '@weekly': '0 0 * * 0',
        '@monthly': '0 0 1 * *',
        '@yearly': '0 0 1 1 *',
        '@annually': '0 0 1 1 *'
    }
    
    if cron in macros:
        return parse_cron(macros[cron])
    
    def parse_range(value):
        if '-' in value:
            start, end = map(int, value.split('-'))
            return range(start, end + 1)
        elif ',' in value:
            return set(map(int, value.split(',')))
        else:
            return {int(value)}
    
    minute_set = parse_range(minute) if minute != '*' else set(range(60))
    hour_set = parse_range(hour) if hour != '*' else set(range(24))
    day_of_month_set = parse_range(day_of_month) if day_of_month != '*' else set(range(1, 32))
    month_set = parse_range(month) if month != '*' else set(range(1, 13))
    day_of_week_set = parse_range(day_of_week) if day_of_week != '*' else set(range(7))
    
    return minute_set, hour_set, day_of_month_set, month_set, day_of_week_set

def next_runs(cron: str, from_time: str, count: int):
    minute_set, hour_set, day_of_month_set, month_set, day_of_week_set = parse_cron(cron)
    
    start_dt = datetime.datetime.fromisoformat(from_time.rstrip('Z')) + datetime.timedelta(seconds=1)
    
    next_times = []
    current_time = start_dt
    while len(next_times) < count:
        if (current_time.minute in minute_set and 
            current_time.hour in hour_set and 
            current_time.day in day_of_month_set and 
            current_time.month in month_set and 
            current_time.weekday() in day_of_week_set):
            
            next_times.append(current_time.isoformat().replace('+00:00', 'Z'))
        
        if current_time.second == 59:
            current_time += datetime.timedelta(minutes=1)
        else:
            current_time += datetime.timedelta(seconds=1)
        
        if (current_time.month != month_set and 
            current_time.day == day_of_month_set and 
            current_time.hour == hour_set and 
            current_time.minute == minute_set):
            
            next_year = start_dt.year + 1 if current_time.month == 12 else start_dt.year
            for month in range(1, 13):
                if (month in month_set or month == '*') and \
                   (current_time.day == day_of_month_set or current_time.day == '*'):
                    try:
                        datetime.datetime(next_year, month, current_time.day)
                        next_times.append(datetime.datetime(next_year, month, current_time.day).isoformat().replace('+00:00', 'Z'))
                    except ValueError:
                        pass
