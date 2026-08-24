import datetime

def _parse_field(field_str: str, min_val: int, max_val: int) -> set[int]:
    values = set()
    for part in field_str.split(','):
        part = part.strip()
        if part == '*':
            values.update(range(min_val, max_val + 1))
        elif '-' in part:
            start_str, end_str = part.split('-', 1)
            start, end = int(start_str), int(end_str)
            if start < min_val or end > max_val or start > end:
                raise ValueError(f"Invalid range: {part}")
            values.update(range(start, end + 1))
        else:
            val = int(part)
            if val < min_val or val > max_val:
                raise ValueError(f"Invalid value: {val}")
            values.add(val)
    return values

def next_runs(cron: str, from_time: str, count: int) -> list[str]:
    fields = cron.strip().split()
    if len(fields) != 5:
        raise ValueError("Cron expression must contain exactly 5 fields")

    mins = _parse_field(fields[0], 0, 59)
    hrs = _parse_field(fields[1], 0, 23)
    doms = _parse_field(fields[2], 1, 31)
    mons = _parse_field(fields[3], 1, 12)
    dows = _parse_field(fields[4], 0, 6)

    from_dt = datetime.datetime.strptime(from_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    current = from_dt + datetime.timedelta(minutes=1)
    results = []

    while len(results) < count:
        cron_dow = (current.weekday() + 1) % 7
        if (current.minute in mins and
            current.hour in hrs and
            current.day in doms and
            current.month in mons and
            cron_dow in dows):
            results.append(current.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
        current += datetime.timedelta(minutes=1)

    return results
