import datetime

def parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
    """Parses a single cron field into a set of allowed integers, supporting steps."""
    allowed = set()
    parts = field.split(',')
    for part in parts:
        # Handle step syntax (e.g., */15 or 1-10/2)
        if '/' in part:
            base_part, step_str = part.split('/')
            step = int(step_str)
        else:
            base_part = part
            step = 1

        # Handle base range (e.g., *, 5, or 1-5)
        if base_part == '*':
            start, end = min_val, max_val
        elif '-' in base_part:
            start_str, end_str = base_part.split('-')
            start, end = int(start_str), int(end_str)
        else:
            start = end = int(base_part)

        # Generate values within the range using the step
        for v in range(start, end + 1, step):
            allowed.add(v)
    return allowed

def next_runs(cron: str, from_time: str, count: int) -> list[str]:
    """
    Calculates the next 'count' occurrences of a 5-position cron expression
    strictly after 'from_time', supporting steps, aliases, and Cron V7 DOM/DOW logic.
    """
    # Handle named macros (aliases)
    macros = {
        "@hourly": "0 * * * *",
        "@daily": "0 0 * * *",
        "@midnight": "0 0 * * *",
        "@weekly": "0 0 * * 0",
        "@monthly": "0 0 1 * *",
        "@yearly": "0 0 1 1 *",
        "@annually": "0 0 1 1 *"
    }
    if cron in macros:
        cron = macros[cron]

    fields = cron.split()
    if len(fields) != 5:
        raise ValueError("Cron expression must have exactly 5 fields.")

    # Parse all fields into sets of allowed values
    m_set = parse_cron_field(fields[0], 0, 59)
    h_set = parse_cron_field(fields[1], 0, 23)
    dom_set = parse_cron_field(fields[2], 1, 31)
    mon_set = parse_cron_field(fields[3], 1, 12)
    dow_set = parse_cron_field(fields[4], 0, 6)

    # Parse from_time (ISO 8601 UTC: "YYYY-MM-DDTHH:MM:SS.000Z")
    base_str = from_time.replace('Z', '')
    dt = datetime.datetime.strptime(base_str, "%Y-%m-%dT%H:%M:%S.%f")
    
    results = []
    # Start checking from the next minute to ensure "strictly later"
    current_dt = dt + datetime.timedelta(minutes=1)

    # Safety limit to prevent infinite loops in case of impossible cron patterns
    max_iterations = 5000000  
    iterations = 0

    while len(results) < count and iterations < max_iterations:
        iterations += 1
        
        # Python weekday: Mon=0, ..., Sun=6. Prompt requirement: Sun=0, ..., Sat=6.
        py_weekday = current_dt.weekday()
        cron_weekday = (py_weekday + 1) % 7

        # Check standard fields (Minute, Hour, Month)
        if (current_dt.minute in m_set and
            current_dt.hour in h_set and
            current_dt.month in mon_set):
            
            # Apply Cron V7 Rule for Day of Month (DOM) and Day of Sundy (DOW)
            dom_match = current_dt.day in dom_set
            dow_match = cron_weekday in dow_set
            
            # If both DOM and DOW are not '*', use OR logic. Otherwise, use AND logic.
            if fields[2] != '*' and fields[4] != '*':
                day_logic_pass = (dom_match or dow_match)
            else:
                day_logic_pass = (dom_match and dow_match)

            if day_logic_pass:
                # Format: YYYY-MM-DDTHH:MM:SS.000Z
                formatted = current_dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
                results.append(formatted)

        current_dt += datetime.timedelta(minutes=1)

    return results
