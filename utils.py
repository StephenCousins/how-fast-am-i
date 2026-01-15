"""
Shared utility functions for the parkrun-scraper project.
Contains common time conversion functions used across multiple modules.
"""

import re
from typing import Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_retry_session(
    retries: int = 3,
    backoff_factor: float = 0.5,
    status_forcelist: tuple = (500, 502, 503, 504),
) -> requests.Session:
    """
    Create a requests session with retry logic for transient failures.

    Args:
        retries: Number of retries for failed requests
        backoff_factor: Wait time multiplier between retries (0.5 = 0.5s, 1s, 2s...)
        status_forcelist: HTTP status codes that trigger a retry

    Returns:
        Configured requests.Session with retry adapter
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def parse_time_to_seconds(time_str: str) -> Optional[int]:
    """
    Convert a time string to seconds.

    Handles formats:
    - MM:SS (e.g., "25:30")
    - H:MM:SS or HH:MM:SS (e.g., "1:23:45" or "01:23:45")

    Args:
        time_str: Time string to parse

    Returns:
        Total seconds as integer, or None if parsing fails
    """
    if not time_str or time_str == '--':
        return None

    time_str = time_str.strip()

    # Remove any trailing letters (e.g., 'c' for chip time indicator)
    time_str = re.sub(r'[a-zA-Z]$', '', time_str)

    parts = time_str.split(':')

    try:
        if len(parts) == 2:
            # MM:SS format
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            # H:MM:SS or HH:MM:SS format
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return None

    return None


def seconds_to_time_str(seconds: int) -> str:
    """
    Convert seconds to a time string.

    Args:
        seconds: Total seconds

    Returns:
        Time string in MM:SS format (if < 1 hour) or H:MM:SS format
    """
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


# Aliases for backwards compatibility with different naming conventions
time_str_to_seconds = parse_time_to_seconds
