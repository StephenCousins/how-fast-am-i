"""
Tests for utility functions.
"""

import pytest
import requests
from utils import (
    parse_time_to_seconds,
    seconds_to_time_str,
    time_str_to_seconds,
    create_retry_session,
)


class TestParseTimeToSeconds:
    """Tests for parse_time_to_seconds function."""

    # Standard MM:SS format
    def test_mm_ss_format(self):
        assert parse_time_to_seconds("25:30") == 1530

    def test_mm_ss_single_digit_minutes(self):
        assert parse_time_to_seconds("5:30") == 330

    def test_mm_ss_zero_seconds(self):
        assert parse_time_to_seconds("20:00") == 1200

    def test_mm_ss_zero_minutes(self):
        assert parse_time_to_seconds("0:45") == 45

    # H:MM:SS format
    def test_h_mm_ss_format(self):
        assert parse_time_to_seconds("1:23:45") == 5025

    def test_hh_mm_ss_format(self):
        assert parse_time_to_seconds("01:23:45") == 5025

    def test_long_hour_format(self):
        assert parse_time_to_seconds("2:30:00") == 9000

    def test_marathon_time(self):
        # 4:21:03 marathon time
        assert parse_time_to_seconds("4:21:03") == 15663

    # Edge cases - empty/null values
    def test_empty_string(self):
        assert parse_time_to_seconds("") is None

    def test_none_value(self):
        assert parse_time_to_seconds(None) is None

    def test_double_dash(self):
        assert parse_time_to_seconds("--") is None

    # Whitespace handling
    def test_leading_whitespace(self):
        assert parse_time_to_seconds("  25:30") == 1530

    def test_trailing_whitespace(self):
        assert parse_time_to_seconds("25:30  ") == 1530

    def test_both_whitespace(self):
        assert parse_time_to_seconds("  25:30  ") == 1530

    # Trailing letters (chip time indicator)
    def test_chip_time_indicator_c(self):
        assert parse_time_to_seconds("25:30c") == 1530

    def test_chip_time_indicator_uppercase(self):
        assert parse_time_to_seconds("1:23:45C") == 5025

    def test_other_trailing_letter(self):
        assert parse_time_to_seconds("25:30x") == 1530

    # Invalid formats
    def test_invalid_format_single_number(self):
        assert parse_time_to_seconds("1234") is None

    def test_invalid_format_text(self):
        assert parse_time_to_seconds("invalid") is None

    def test_invalid_format_non_numeric(self):
        assert parse_time_to_seconds("ab:cd") is None

    def test_invalid_format_too_many_colons(self):
        assert parse_time_to_seconds("1:2:3:4") is None

    # Real-world parkrun times
    def test_fast_5k_time(self):
        # 18:16 - fast 5K
        assert parse_time_to_seconds("18:16") == 1096

    def test_average_5k_time(self):
        # 25:00 - average 5K
        assert parse_time_to_seconds("25:00") == 1500

    def test_slower_5k_time(self):
        # 35:45 - slower 5K
        assert parse_time_to_seconds("35:45") == 2145


class TestSecondsToTimeStr:
    """Tests for seconds_to_time_str function."""

    # Under 1 hour (MM:SS format)
    def test_basic_mm_ss(self):
        assert seconds_to_time_str(1530) == "25:30"

    def test_single_digit_minutes(self):
        assert seconds_to_time_str(330) == "5:30"

    def test_zero_seconds(self):
        assert seconds_to_time_str(1200) == "20:00"

    def test_zero_minutes(self):
        assert seconds_to_time_str(45) == "0:45"

    def test_zero(self):
        assert seconds_to_time_str(0) == "0:00"

    def test_just_under_hour(self):
        assert seconds_to_time_str(3599) == "59:59"

    # Over 1 hour (H:MM:SS format)
    def test_exactly_one_hour(self):
        assert seconds_to_time_str(3600) == "1:00:00"

    def test_h_mm_ss_format(self):
        assert seconds_to_time_str(5025) == "1:23:45"

    def test_two_hours(self):
        assert seconds_to_time_str(9000) == "2:30:00"

    def test_marathon_time(self):
        # 4:21:03 marathon time
        assert seconds_to_time_str(15663) == "4:21:03"

    def test_long_race(self):
        # 5:30:00
        assert seconds_to_time_str(19800) == "5:30:00"

    # Padding verification
    def test_single_digit_seconds_padded(self):
        assert seconds_to_time_str(1505) == "25:05"

    def test_single_digit_minutes_and_seconds_in_hours(self):
        assert seconds_to_time_str(3665) == "1:01:05"

    # Real-world times
    def test_fast_5k(self):
        assert seconds_to_time_str(1096) == "18:16"

    def test_half_marathon(self):
        # 1:23:27
        assert seconds_to_time_str(5007) == "1:23:27"


class TestRoundTrip:
    """Test that converting back and forth preserves values."""

    def test_roundtrip_mm_ss(self):
        original = "25:30"
        seconds = parse_time_to_seconds(original)
        result = seconds_to_time_str(seconds)
        assert result == original

    def test_roundtrip_h_mm_ss(self):
        original = "1:23:45"
        seconds = parse_time_to_seconds(original)
        result = seconds_to_time_str(seconds)
        assert result == original

    def test_roundtrip_seconds(self):
        original = 5025
        time_str = seconds_to_time_str(original)
        result = parse_time_to_seconds(time_str)
        assert result == original

    def test_roundtrip_various_times(self):
        times = ["18:16", "25:00", "35:45", "1:00:00", "2:55:42", "4:21:03"]
        for time in times:
            seconds = parse_time_to_seconds(time)
            result = seconds_to_time_str(seconds)
            assert result == time, f"Round trip failed for {time}"


class TestAlias:
    """Test that the alias works correctly."""

    def test_alias_same_function(self):
        assert time_str_to_seconds is parse_time_to_seconds

    def test_alias_returns_same_result(self):
        assert time_str_to_seconds("25:30") == parse_time_to_seconds("25:30")


class TestCreateRetrySession:
    """Tests for create_retry_session function."""

    def test_returns_session(self):
        session = create_retry_session()
        assert isinstance(session, requests.Session)

    def test_default_parameters(self):
        session = create_retry_session()
        # Verify adapters are mounted
        assert "http://" in session.adapters
        assert "https://" in session.adapters

    def test_custom_retries(self):
        session = create_retry_session(retries=5)
        adapter = session.get_adapter("https://")
        assert adapter.max_retries.total == 5

    def test_custom_backoff_factor(self):
        session = create_retry_session(backoff_factor=1.0)
        adapter = session.get_adapter("https://")
        assert adapter.max_retries.backoff_factor == 1.0

    def test_custom_status_forcelist(self):
        session = create_retry_session(status_forcelist=(429, 500, 503))
        adapter = session.get_adapter("https://")
        assert 429 in adapter.max_retries.status_forcelist
        assert 500 in adapter.max_retries.status_forcelist
        assert 503 in adapter.max_retries.status_forcelist

    def test_http_and_https_adapters_mounted(self):
        session = create_retry_session()
        http_adapter = session.get_adapter("http://example.com")
        https_adapter = session.get_adapter("https://example.com")
        # Both should have retry strategy
        assert http_adapter.max_retries.total == 3  # default
        assert https_adapter.max_retries.total == 3  # default

    def test_allowed_methods(self):
        session = create_retry_session()
        adapter = session.get_adapter("https://")
        assert "GET" in adapter.max_retries.allowed_methods
        assert "POST" in adapter.max_retries.allowed_methods
