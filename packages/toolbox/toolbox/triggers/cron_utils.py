from datetime import datetime, timezone

from croniter import croniter


def calculate_next_run_time(cron_schedule: str, from_time: datetime) -> datetime:
    """Calculate the next run time for a cron schedule from a given time.

    Args:
        cron_schedule: Valid cron expression
        from_time: UTC datetime to calculate from

    Returns:
        Next run time as UTC datetime

    Raises:
        ValueError: If cron schedule is invalid
    """
    if not croniter.is_valid(cron_schedule):
        raise ValueError(f"Invalid cron schedule: {cron_schedule}")

    # Ensure from_time is timezone-aware (UTC)
    if from_time.tzinfo is None:
        from_time = from_time.replace(tzinfo=timezone.utc)
    elif from_time.tzinfo != timezone.utc:
        from_time = from_time.astimezone(timezone.utc)

    iter = croniter(cron_schedule, from_time)
    next_run = iter.get_next(datetime)

    # Ensure result is UTC
    if next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=timezone.utc)
    elif next_run.tzinfo != timezone.utc:
        next_run = next_run.astimezone(timezone.utc)

    return next_run


def is_valid_cron(cron_schedule: str) -> bool:
    """Check if a cron schedule is valid."""
    return croniter.is_valid(cron_schedule)
