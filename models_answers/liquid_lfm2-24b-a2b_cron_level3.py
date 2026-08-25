import datetime
from typing import List, Tuple, Union, Dict

def parse_cron(cron: str) -> Tuple[Union[int, str], ...]:
    parts = cron.strip().split()
    if len(parts) != 5:
        raise ValueError("Cron must have exactly 5 fields")
    def parse_field(field: str) -> Union[int, List[int], Tuple[int, int], str]:
        if field == '*':
            return '*'
        if '-' in field:
            a, b = field.split('-')
            a = int(a.strip() or 0)
            b = int(b.strip() or 100)
            return (a, b)
        if ',' in field:
            return [int(x.strip()) for x in field.split(',')]
        if '*' in field:
            raise ValueError("Cannot mix * with other specifiers")
        if '.' in field:
            raise ValueError("Dot not allowed in cron field")
        try:
            return int(field)
        except ValueError:
            raise ValueError(f"Invalid value in cron field: {field}")
    return tuple(parse_field(p) for p in parts)

def parse_step(range_part: str) -> Union[int, Tuple[int, int], None]:
    if '*' in range_part:
        return None
    if '-' in range_part:
        a, b = range_part.split('-')
        a = int(a.strip())
        b = int(b.strip())
        return (a, b)
    if '/' in range_part:
        parts = range_part.split('/')
        a = int(parts[0].strip())
        n = int(parts[1].strip())
        return (a, n)
    return None

def expand_named_macros(cron: str) -> str:
    macros = {
        '@hourly': '0 * * * *',
        '@daily': '0 0 * * *',
        '@midnight': '0 0 * * *',
        '@weekly': '0 0 * * 0',
        '@monthly': '0 0 1 * *',
        '@yearly': '0 0 1 1 *',
        '@annually': '0 0 1 1 *'
    }
    for name, value in macros.items():
        if cron.startswith(name + ':'):
            return cron.replace(name + ':', value)
    return cron

def is_leap_year(year: int) -> bool:
    return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

def next_runs(cron: str, from_time: str, count: int) -> List[str]:
    cron = expand_named_macros(cron)
    cron_parts = parse_cron(cron)
    dt = datetime.datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    start = dt + datetime.timedelta(seconds=1)
    results = []
    current = start
    year = dt.year

    while len(results) < count:
        # Adjust for leap year if checking Feb 29 in non-leap year
        if cron_parts[4] == '29' and cron_parts[4] != '*':
            if not is_leap_year(current.year):
                current += datetime.timedelta(days=1)
                continue
        # Adjust day of month for February in leap years
        if (cron_parts[2] == 29 and cron_parts[2] != '*' and current.month == 2 and not is_leap_year(current.year)):
            current += datetime.timedelta(days=1)
            continue

        if matches(cron_parts, current):
            results.append(current.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        current += datetime.timedelta(seconds=1)
        # Prevent infinite loop in case cron never matches
        if len(results) == 0 and current > dt + datetime.timedelta(days=365):
            break
    return results

def matches(cron_parts: Tuple[Union[int, str], ...], dt: datetime.datetime) -> bool:
    minute, hour, day_m, month, day_d = cron_parts
    m = dt.minute
    h = dt.hour
    dm = dt.day
    mo = dt.month
    dd = dt.weekday()  # Monday=0 ... Sunday=6

    def in_range(v, l, r):
        if isinstance(v, int):
            return l <= v <= r
        if isinstance(v, tuple):
            a, b = l, r
            return a <= v <= b
        if isinstance(v, list):
            return any(in_range(x, l, r) for x in v)
        return False

    # Step logic
    step_m = parse_step(range(m))
    step_h = parse_step(range(h))
    step_dm = parse_step(range(dm))
    step_dd = parse_step(range(day_d))

    def valid_range(val, l, r):
        if isinstance(val, list):
            return any(in_range(x, l, r) for x in val)
        elif isinstance(val, tuple):
            a, b = l, r
            return a <= val <= b
        else:
            return l <= val <= r

    # Check minute
    if not in_range(m, *minute if minute != '*' else (0, 59), *minute if minute != '*' else (0, 59)):
        return False
    if step_m is not None:
        if not (m % step_m[1] == 0 and in_range(m, step_m[0], step_m[1])):
            return False

    # Check hour
    if not in_range(h, *hour if hour != '*' else (0, 23), *hour if hour != '*' else (0, 23)):
        return False
    if step_h is not None:
        if not (h % step_h[1] == 0 and in_range(h, step_h[0], step_h[1])):
            return False

    # Check day of month
    if not valid_range(dm, *day_m if day_m != '*' else (1, month), *day_m if day_m != '*' else (1, month)):
        return False
    if step_dm is not None:
        if not (dm % step_dm[1] == 0 and in_range(dm, step_dm[0], step_dm[1])):
            return False

    # Check month
    if not valid_range(month, *day_m if day_m != '*' else (1, 12), *day_m if day_m != '*' else (1, 12)):
        return False
    if step_mm is not None:
        if not (month % step_mm[1] == 0 and in_range(month, step_mm[0], step_mm[1])):
            return False

    # Check day of week
    if not valid_range(day_d, *day_d if day_d != '*' else (0, 6), *day_d if day_d != '*' else (0, 6)):
        return False
    if step_dd is not None:
        if not (dd % step_dd[1] == 0 and in_range(dd, step_dd[0], step_dd[1])):
            return False

    # If any field is *, enforce exact match for that field only when others are not *
    if cron_parts[2] != '*' or cron_parts[4] != '*':
        if not in_range(dm, *cron_parts[2], *cron_parts[2]):
            return False
        if not in_range(day_d, *cron_parts[4], *cron_parts[4]):
            return False

    return True
