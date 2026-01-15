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


# =============================================================================
# Athlete ID Validation
# =============================================================================

# Maximum lengths for athlete IDs (prevents abuse and potential DoS)
MAX_PARKRUN_ID_LENGTH = 10  # Parkrun IDs are typically 6-7 digits
MAX_PO10_ID_LENGTH = 10     # Power of 10 IDs are typically 6 digits
MAX_ATHLINKS_ID_LENGTH = 12 # Athlinks IDs can be longer

# Maximum reasonable values (sanity check)
MAX_ATHLETE_ID_VALUE = 99999999999  # 11 digits max


class ValidationResult:
    """Result of athlete ID validation."""

    def __init__(self, is_valid: bool, error_message: Optional[str] = None, sanitized_id: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message
        self.sanitized_id = sanitized_id

    def __bool__(self):
        return self.is_valid


def validate_athlete_id(
    athlete_id: str,
    platform: str = "parkrun",
    max_length: Optional[int] = None,
) -> ValidationResult:
    """
    Validate an athlete ID for a given platform.

    Args:
        athlete_id: The athlete ID to validate
        platform: One of 'parkrun', 'po10', 'athlinks'
        max_length: Optional custom max length override

    Returns:
        ValidationResult with is_valid, error_message, and sanitized_id
    """
    # Determine max length based on platform
    if max_length is None:
        max_lengths = {
            'parkrun': MAX_PARKRUN_ID_LENGTH,
            'po10': MAX_PO10_ID_LENGTH,
            'athlinks': MAX_ATHLINKS_ID_LENGTH,
        }
        max_length = max_lengths.get(platform, MAX_PARKRUN_ID_LENGTH)

    # Platform-specific names for error messages
    platform_names = {
        'parkrun': 'Parkrun',
        'po10': 'Power of 10',
        'athlinks': 'Athlinks',
    }
    platform_name = platform_names.get(platform, 'Athlete')

    # Check for None or non-string
    if athlete_id is None:
        return ValidationResult(False, f"Please enter a {platform_name} athlete ID")

    if not isinstance(athlete_id, str):
        return ValidationResult(False, f"{platform_name} ID must be a string")

    # Strip whitespace
    sanitized = athlete_id.strip()

    # Check for empty string
    if not sanitized:
        return ValidationResult(False, f"Please enter a {platform_name} athlete ID")

    # Check for non-numeric characters
    if not sanitized.isdigit():
        return ValidationResult(
            False,
            f"{platform_name} ID should contain only numbers (e.g., 123456)"
        )

    # Check length
    if len(sanitized) > max_length:
        return ValidationResult(
            False,
            f"{platform_name} ID is too long (maximum {max_length} digits)"
        )

    # Check for leading zeros that might indicate an issue (but allow them)
    # Just ensure the value is reasonable
    try:
        id_value = int(sanitized)
        if id_value <= 0:
            return ValidationResult(
                False,
                f"{platform_name} ID must be a positive number"
            )
        if id_value > MAX_ATHLETE_ID_VALUE:
            return ValidationResult(
                False,
                f"{platform_name} ID is too large"
            )
    except ValueError:
        return ValidationResult(
            False,
            f"{platform_name} ID is not a valid number"
        )

    return ValidationResult(True, None, sanitized)


def validate_parkrun_id(athlete_id: str) -> ValidationResult:
    """Validate a Parkrun athlete ID."""
    return validate_athlete_id(athlete_id, platform="parkrun")


def validate_po10_id(athlete_id: str) -> ValidationResult:
    """Validate a Power of 10 athlete ID."""
    return validate_athlete_id(athlete_id, platform="po10")


def validate_athlinks_id(athlete_id: str) -> ValidationResult:
    """Validate an Athlinks athlete ID."""
    return validate_athlete_id(athlete_id, platform="athlinks")
