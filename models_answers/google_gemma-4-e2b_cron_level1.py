import datetime
import re
from typing import List

def parse_cron_field(field: str) -> set[int]:
    """
    Parses a single cron field string into a set of allowed integer values,
    handling '*', lists, and ranges.
    """
    if field == '*':
        # '*' matches all possible values for that field
        return set(range(60)) if field == 'minute' else set(range(24)) if field == 'hour' else set(range(31)) if field == 'day_of_month' else set(range(1, 13)) if field == 'month' else set(range(7))
    
    values = set()
    parts = field.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle ranges (e.g., 9-17)
            start_str, end_str = part.split('-')
            start = int(start_str)
            end = int(end_str)
            values.update(range(start, end + 1))
        else:
            # Handle single values (e.g., 5)
            try:
                values.add(int(part))
            except ValueError:
                pass # Ignore invalid parts

    return values

def parse_cron(cron_str: str) -> List[set[int]]:
    """
    Parses the full cron string into a list of sets, one for each field.
    Returns an empty list if parsing fails or fields are missing.
    """
    fields = cron_str.split()
    if len(fields) != 5:
        raise ValueError("Cron expression must have exactly 5 fields.")

    parsed_fields = []
    for field in fields:
        parsed_fields.append(parse_cron_field(field))
    
    return parsed_fields

def is_valid_time(dt: datetime.datetime, cron_fields: List[set[int]]) -> bool:
    """
    Checks if a given datetime object matches the parsed cron constraints.
    """
    # 1. Minute (0-59)
    if dt.minute not in cron_fields[0]:
        return False
    
    # 2. Hour (0-23)
    if dt.hour not in cron_fields[1]:
        return False

    # 3. Day of Month (1-31)
    if not (1 <= dt.day <= 31):
        return False
    if dt.day not in cron_fields[2]:
        return False

    # 4. Month (1-12)
    if not (1 <= dt.month <= 12):
        return False
    if dt.month not in cron_fields[3]:
        return False

    # 5. Day of Week (0=Sun, 6=Sat)
    if not (0 <= dt.weekday() <= 6):
        return False
    if dt.weekday() not in cron_fields[4]:
        return False
        
    return True


def next_runs(cron: str, from_time: str, count: int) -> List[str]:
    """
    Finds the next 'count' occurrences of a cron schedule starting after from_time.

    Args:
        cron: The 5-position cron expression string.
        from_time: The starting datetime in ISO 8601 UTC format.
        count: The number of subsequent runs to find.

    Returns:
        A list of ISO 8601 UTC strings for the next run times.
    """
    try:
        parsed_fields = parse_cron(cron)
    except ValueError as e:
        # In a real application, handle this error more gracefully
        raise ValueError(f"Invalid cron format: {e}")

    try:
        start_dt = datetime.datetime.fromisoformat(from_time.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError("Invalid from_time format. Must be ISO 8601 UTC.")

    current_dt = start_dt
    results = []
    
    # Set a reasonable upper bound to prevent infinite loops in case of bad cron logic, 
    # though theoretically not needed if the schedule is valid.
    max_iterations = 50000 
    iteration_count = 0

    while len(results) < count and iteration_count < max_iterations:
        # Ensure we only check times strictly after from_time
        if current_dt > start_dt:
            if is_valid_time(current_dt, parsed_fields):
                # Found a valid run time
                results.append(current_dt.isoformat().replace('+00:00', 'Z'))
        
        # Advance time by one minute to check the next potential run
        current_dt += datetime.timedelta(minutes=1)
        iteration_count += 1

    if len(results) < count:
        # This indicates that we failed to find enough runs within the iteration limit,
        # which usually means the schedule is extremely sparse or the time span is too large.
        pass # Return what was found

    return results

if __name__ == '__main__':
    # --- Example Usage ---

    # Cron example: Every Monday at 10:30 AM (10:30)
    CRON_EXPR = "30 10 * * 1"
    
    # Start time: August 18, 2026, 10:00 AM UTC
    FROM_TIME = "2026-08-18T10:00:00.000Z"
    COUNT = 5

    print(f"Cron Expression: {CRON_EXPR}")
    print(f"Starting Time: {FROM_TIME}")
    print(f"Finding next {COUNT} runs:\n")

    try:
        run_times = next_runs(CRON_EXPR, FROM_TIME, COUNT)
        for i, rt in enumerate(run_times):
            print(f"{i+1}. {rt}")
            
    except ValueError as e:
        print(f"Error: {e}")

    print("\n--- Example 2: Complex Range ---")
    # Cron example: Every hour from 9 to 17, every day of the month, every month.
    CRON_EXPR_RANGE = "9-17 * * * *"
    FROM_TIME_2 = "2024-01-01T00:00:00.000Z"
    COUNT_2 = 5

    print(f"Cron Expression: {CRON_EXPR_RANGE}")
    print(f"Starting Time: {FROM_TIME_2}")
    print(f"Finding next {COUNT_2} runs:\n")

    try:
        run_times_2 = next_runs(CRON_EXPR_RANGE, FROM_TIME_2, COUNT_2)
        for i, rt in enumerate(run_times_2):
            print(f"{i+1}. {rt}")
            
    except ValueError as e:
        print(f"Error: {e}")
