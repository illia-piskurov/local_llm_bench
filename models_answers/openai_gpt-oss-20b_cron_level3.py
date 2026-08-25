import datetime
from typing import List, Set, Tuple

# Alias mapping for named macros
_ALIAS_MAP = {
    "@hourly":   "0 * * * *",
    "@daily":    "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@weekly":   "0 0 * * 0",
    "@monthly":  "0 0 1 * *",
    "@yearly":   "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
}

def _parse_simple(part: str, min_val: int, max_val: int) -> Set[int]:
    """Parse a part without steps."""
    if part == '*':
        return set(range(min_val, max_val + 1))
    result = set()
    for sub in part.split(','):
        if '-' in sub:
            a, b = map(int, sub.split('-'))
            result.update(range(a, b + 1))
        else:
            result.add(int(sub))
    return result

def parse_field(field: str, min_val: int, max_val: int) -> Set[int]:
    """Parse a cron field supporting steps."""
    result = set()
    for part in field.split(','):
        if '/' in part:
            base_part, step_str = part.split('/')
            step = int(step_str)
            base_set = _parse_simple(base_part, min_val, max_val)
            start = min(base_set)  # first value in the base set
            result.update(v for v in base_set if (v - start) % step == 0)
        else:
            result.update(_parse_simple(part, min_val, max_val))
    return result

def parse_cron(cron: str) -> Tuple[Set[int], Set[int], Set[int], Set[int], Set[int], bool, bool]:
    """Parse cron expression into sets of allowed values."""
    # Resolve named macro if present
    cron = _ALIAS_MAP.get(cron.strip(), cron)
    minute_str, hour_str, dom_str, month_str, dow_str = cron.split()
    minutes = parse_field(minute_str, 0, 59)
    hours   = parse_field(hour_str, 0, 23)
    days_mo = parse_field(dom_str, 1, 31)
    months  = parse_field(month_str, 1, 12)
    days_wk = parse_field(dow_str, 0, 6)
    dom_star = dom_str == '*'
    dow_star = dow_str == '*'
    return minutes, hours, days_mo, months, days_wk, dom_star, dow_star

def next_runs(cron: str, from_time: str, count: int) -> List[str]:
    minutes, hours, days_mo, months, days_wk, dom_star, dow_star = parse_cron(cron)
    start_dt = datetime.datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    # Start checking from the next minute
    current = (start_dt + datetime.timedelta(minutes=1)).replace(second=0, microsecond=0)

    results: List[str] = []
    while len(results) < count:
        if (
            current.minute in minutes and
            current.hour   in hours   and
            current.month  in months  and
            current.day    in days_mo and
            current.weekday() % 7 in days_wk
        ):
            # Apply Cron V7 day rule
            dom_match = current.day in days_mo
            dow_match = current.weekday() % 7 in days_wk
            if not dom_star and not dow_star:
                day_ok = dom_match or dow_match
            else:
                day_ok = dom_match if dow_star else dow_match

            if day_ok:
                iso_str = current.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                results.append(iso_str)
        current += datetime.timedelta(minutes=1)
    return results
