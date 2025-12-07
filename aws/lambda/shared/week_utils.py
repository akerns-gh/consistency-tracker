"""
Week ID calculation utilities.
"""

from datetime import datetime, timedelta


def get_week_id(date: datetime = None) -> str:
    """
    Get week ID in format YYYY-WW (e.g., "2025-W03").
    
    Weeks start on Monday.
    
    Args:
        date: Date to calculate week for (defaults to today)
    
    Returns:
        Week ID string in format YYYY-WW
    """
    if date is None:
        date = datetime.utcnow()
    
    # Set to start of day
    d = date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get Monday of the week
    day_of_week = d.weekday()  # 0 = Monday, 6 = Sunday
    days_to_monday = (day_of_week) % 7
    monday = d - timedelta(days=days_to_monday)
    
    # Calculate week number (1-53)
    year = monday.year
    jan_1 = datetime(year, 1, 1)
    
    # Get Monday of the week containing Jan 1
    jan_1_weekday = jan_1.weekday()
    first_monday = jan_1 - timedelta(days=jan_1_weekday)
    
    # Calculate week number
    days_diff = (monday - first_monday).days
    week_num = (days_diff // 7) + 1
    
    # Handle edge case: if week 0, it's actually week 52/53 of previous year
    if week_num == 0:
        prev_year = year - 1
        prev_dec_31 = datetime(prev_year, 12, 31)
        return get_week_id(prev_dec_31)
    
    return f"{year}-W{week_num:02d}"


def get_week_dates(week_id: str) -> tuple:
    """
    Get Monday and Sunday dates for a week ID.
    
    Args:
        week_id: Week ID in format YYYY-WW
    
    Returns:
        Tuple of (monday_date, sunday_date) as datetime objects
    """
    year_str, week_str = week_id.split("-W")
    year = int(year_str)
    week_num = int(week_str)
    
    # Get January 1 of the year
    jan_1 = datetime(year, 1, 1)
    jan_1_weekday = jan_1.weekday()
    first_monday = jan_1 - timedelta(days=jan_1_weekday)
    
    # Calculate Monday of the target week
    weeks_to_add = week_num - 1
    monday = first_monday + timedelta(weeks=weeks_to_add)
    sunday = monday + timedelta(days=6)
    
    return (monday, sunday)


def get_current_week_id() -> str:
    """Get the current week ID."""
    return get_week_id()

