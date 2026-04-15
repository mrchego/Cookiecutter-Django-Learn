import datetime
# → Imports Python's datetime module for date and time operations.

# What it does:
# Converts a date object (without time) to a datetime object at midnight UTC (00:00:00) with UTC timezone.

def convert_to_utc_date_time(date) -> None | datetime.datetime:
#     → Function that takes a date and returns a datetime or None
# → Return type: either None or a datetime object
    """Convert date into utc date time."""
    if date is None:
        return None
    # → If input is None, return None (no conversion)
    return datetime.datetime.combine(
        date, datetime.datetime.min.time(), tzinfo=datetime.UTC
    )
# → datetime.datetime.combine() = Combines a date and time into a datetime
# → date = The date part (e.g., 2024-01-15)
# → datetime.datetime.min.time() = Minimum time (00:00:00)
# → tzinfo=datetime.UTC = Sets UTC timezone
# → Result: datetime(2024, 1, 15, 0, 0, 0, tzinfo=UTC)
