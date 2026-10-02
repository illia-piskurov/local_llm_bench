import datetime
import calendar
from typing import List, Tuple, Union, Set

def parse_cron(cron: str) -> Tuple[Union[int, str], ...]:
    parts = cron.strip().split()
    if len(parts) != 5:
        raise ValueError("Cron must have exactly 5 fields")
    def parse_field(field: str) -> Union[int, List[int], Tuple[int, int]]:
        if field == '*':
            return '*'
        if '-' in field:
            a, b = field.split('-')
            a = int(a.strip() or 0)
            b = int(b.strip() or 100)  # max value
            return (a, b)
        if ',' in field:
            return [int(x.strip()) for x in field.split(',')]
        if '.' in field:
            raise ValueError("Dot not allowed in cron field")
        try:
            return int(field)
        except ValueError:
            raise ValueError(f"Invalid value in cron field: {field}")
    return tuple(parse_field(p) for p in parts)

def generate_candidates(range_type: Union[str, Tuple[int, int]], start: int, end: int) -> List[int]:
    if range_type == '*':
        return list(range(start, end + 1))
    if isinstance(range_type, tuple):
        a, b = range_type
        return list(range(a, b + 1))
    return []

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

    if not in_range(m, minute, minute): return False
    if not in_range(h, hour, hour): return False
    if not in_range(dm, day_m, month): return False
    if not in_range(day_d, 0, 6): return False
    return True

def next_runs(cron: str, from_time: str, count: int) -> List[str]:
    cron_parts = parse_cron(cron)
    dt = datetime.datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    start = dt + datetime.timedelta(seconds=1)
    results = []
    current = start
    while len(results) < count:
        if matches(cron_parts, current):
            results.append(current.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        current += datetime.timedelta(seconds=1)
        # Prevent infinite loop in case cron never matches
        if len(results) == 0 and current > dt + datetime.timedelta(days=365):
            break
    return results
