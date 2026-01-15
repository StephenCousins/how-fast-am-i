"""
Tests for async_scraper.py - async scraping functionality.
"""

import asyncio
import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from aioresponses import aioresponses

from async_scraper import (
    AsyncParkrunScraper,
    AsyncPowerOf10Scraper,
    fetch_multiple_athletes,
    run_async,
)


# Configure pytest-asyncio to auto mode
pytest_plugins = ('pytest_asyncio',)


# Sample HTML responses for testing
SAMPLE_PARKRUN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test Athlete</title></head>
<body>
<h2>John Smith - All Results</h2>
<table id="results">
    <tr>
        <th>Event</th>
        <th>Run Date</th>
        <th>Run Number</th>
        <th>Position</th>
        <th>Time</th>
        <th>Age Grade</th>
    </tr>
    <tr>
        <td>parkrun Event</td>
        <td>01/01/2026</td>
        <td>100</td>
        <td>50</td>
        <td>25:30</td>
        <td>55.0%</td>
    </tr>
    <tr>
        <td>Another parkrun</td>
        <td>08/01/2026</td>
        <td>101</td>
        <td>45</td>
        <td>24:15</td>
        <td>57.5%</td>
    </tr>
</table>
</body>
</html>
"""

SAMPLE_PO10_HTML = """
<!DOCTYPE html>
<html>
<head><title>Power of 10</title></head>
<body>
<div id="athletename">Jane Doe</div>
<div id="club">Test Running Club</div>
<table class="results">
    <tr><td>5K</td><td>20:00</td></tr>
    <tr><td>10K</td><td>42:00</td></tr>
</table>
</body>
</html>
"""

EMPTY_HTML = """
<!DOCTYPE html>
<html>
<head><title>No Results</title></head>
<body>
<h2>Unknown Athlete</h2>
<p>No results found</p>
</body>
</html>
"""


class TestAsyncParkrunScraperInit:
    """Tests for AsyncParkrunScraper initialization."""

    def test_init_without_api_key(self):
        """Test initialization without ScraperAPI key."""
        with patch.dict(os.environ, {}, clear=True):
            scraper = AsyncParkrunScraper()
            assert scraper.scraper_api_key is None
            assert scraper._session is None

    def test_init_with_api_key(self):
        """Test initialization with ScraperAPI key."""
        with patch.dict(os.environ, {'SCRAPER_API_KEY': 'test_key'}):
            scraper = AsyncParkrunScraper()
            assert scraper.scraper_api_key == 'test_key'

    def test_base_url(self):
        """Test BASE_URL is correctly set."""
        scraper = AsyncParkrunScraper()
        assert scraper.BASE_URL == "https://www.parkrun.org.uk/parkrunner"

    def test_headers_set(self):
        """Test HEADERS dictionary is properly configured."""
        scraper = AsyncParkrunScraper()
        assert 'User-Agent' in scraper.HEADERS
        assert 'Accept' in scraper.HEADERS


class TestAsyncParkrunScraperUrlGeneration:
    """Tests for URL generation logic."""

    def test_get_url_without_api_key(self):
        """Test URL generation without ScraperAPI."""
        with patch.dict(os.environ, {}, clear=True):
            scraper = AsyncParkrunScraper()
            url = scraper._get_url("https://example.com/test")
            assert url == "https://example.com/test"

    def test_get_url_with_api_key(self):
        """Test URL generation with ScraperAPI."""
        with patch.dict(os.environ, {'SCRAPER_API_KEY': 'test_key'}):
            scraper = AsyncParkrunScraper()
            url = scraper._get_url("https://example.com/test")
            assert "api.scraperapi.com" in url
            assert "api_key=test_key" in url
            assert "https%3A%2F%2Fexample.com%2Ftest" in url


class TestAsyncParkrunScraperSessionManagement:
    """Tests for session management."""

    @pytest.mark.asyncio
    async def test_context_manager_creates_session(self):
        """Test that context manager creates session."""
        async with AsyncParkrunScraper() as scraper:
            assert scraper._session is not None
            assert not scraper._session.closed

    @pytest.mark.asyncio
    async def test_context_manager_closes_session(self):
        """Test that context manager closes session on exit."""
        scraper = AsyncParkrunScraper()
        async with scraper:
            session = scraper._session
        assert session.closed

    @pytest.mark.asyncio
    async def test_ensure_session_creates_new_session(self):
        """Test _ensure_session creates session when none exists."""
        scraper = AsyncParkrunScraper()
        assert scraper._session is None
        await scraper._ensure_session()
        assert scraper._session is not None
        await scraper.close()

    @pytest.mark.asyncio
    async def test_ensure_session_recreates_closed_session(self):
        """Test _ensure_session recreates closed session."""
        scraper = AsyncParkrunScraper()
        await scraper._ensure_session()
        first_session = scraper._session
        await scraper.close()
        assert first_session.closed
        await scraper._ensure_session()
        assert scraper._session is not None
        assert not scraper._session.closed
        await scraper.close()

    @pytest.mark.asyncio
    async def test_close_handles_none_session(self):
        """Test close() handles None session gracefully."""
        scraper = AsyncParkrunScraper()
        await scraper.close()  # Should not raise


class TestAsyncParkrunScraperGetAthleteResults:
    """Tests for get_athlete_results method."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful athlete data fetch."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/123456/all/",
                body=SAMPLE_PARKRUN_HTML,
                status=200
            )
            async with AsyncParkrunScraper() as scraper:
                result = await scraper.get_athlete_results("123456")
                assert result['error'] is None
                assert result['name'] == "John Smith"
                assert result['athlete_id'] == "123456"
                assert result['total_runs'] == 2

    @pytest.mark.asyncio
    async def test_403_forbidden(self):
        """Test handling of 403 Forbidden response."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/123456/all/",
                status=403
            )
            async with AsyncParkrunScraper() as scraper:
                result = await scraper.get_athlete_results("123456")
                assert 'Access denied' in result['error']
                assert result['athlete_id'] == "123456"

    @pytest.mark.asyncio
    async def test_404_not_found(self):
        """Test handling of 404 Not Found response."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/999999/all/",
                status=404
            )
            async with AsyncParkrunScraper() as scraper:
                result = await scraper.get_athlete_results("999999")
                assert 'not found' in result['error']
                assert result['athlete_id'] == "999999"

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout error."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/123456/all/",
                exception=asyncio.TimeoutError()
            )
            async with AsyncParkrunScraper() as scraper:
                result = await scraper.get_athlete_results("123456")
                assert 'timed out' in result['error']

    @pytest.mark.asyncio
    async def test_client_error(self):
        """Test handling of client error."""
        import aiohttp
        with aioresponses() as mocked:
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/123456/all/",
                exception=aiohttp.ClientError("Connection failed")
            )
            async with AsyncParkrunScraper() as scraper:
                result = await scraper.get_athlete_results("123456")
                assert 'Failed to fetch' in result['error']


class TestAsyncParkrunScraperParsing:
    """Tests for HTML parsing functionality."""

    def test_parse_athlete_name(self):
        """Test parsing athlete name from HTML."""
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(SAMPLE_PARKRUN_HTML, "123456")
        assert result['name'] == "John Smith"

    def test_parse_results_table(self):
        """Test parsing results table."""
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(SAMPLE_PARKRUN_HTML, "123456")
        assert len(result['results']) == 2
        assert result['results'][0]['time'] == "25:30"
        assert result['results'][1]['time'] == "24:15"

    def test_parse_time_seconds(self):
        """Test that time_seconds is calculated."""
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(SAMPLE_PARKRUN_HTML, "123456")
        assert result['results'][0]['time_seconds'] == 1530  # 25:30
        assert result['results'][1]['time_seconds'] == 1455  # 24:15

    def test_parse_no_results_table(self):
        """Test parsing when no results table found."""
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(EMPTY_HTML, "123456")
        assert 'Could not find results table' in result['error']


class TestAsyncPowerOf10ScraperInit:
    """Tests for AsyncPowerOf10Scraper initialization."""

    def test_init(self):
        """Test basic initialization."""
        scraper = AsyncPowerOf10Scraper()
        assert scraper._session is None

    def test_base_url(self):
        """Test BASE_URL is correctly set."""
        scraper = AsyncPowerOf10Scraper()
        assert "thepowerof10.info" in scraper.BASE_URL


class TestAsyncPowerOf10ScraperSessionManagement:
    """Tests for PO10 scraper session management."""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test context manager creates and closes session."""
        scraper = AsyncPowerOf10Scraper()
        async with scraper:
            assert scraper._session is not None
            session = scraper._session
        assert session.closed


class TestAsyncPowerOf10ScraperGetAthlete:
    """Tests for get_athlete_by_id method."""

    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout error."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.thepowerof10.info/athletes/profile.aspx?athleteid=123456",
                exception=asyncio.TimeoutError()
            )
            async with AsyncPowerOf10Scraper() as scraper:
                result = await scraper.get_athlete_by_id("123456")
                assert 'timed out' in result['error']

    @pytest.mark.asyncio
    async def test_client_error(self):
        """Test handling of client error."""
        import aiohttp
        with aioresponses() as mocked:
            mocked.get(
                "https://www.thepowerof10.info/athletes/profile.aspx?athleteid=123456",
                exception=aiohttp.ClientError("Connection failed")
            )
            async with AsyncPowerOf10Scraper() as scraper:
                result = await scraper.get_athlete_by_id("123456")
                assert 'Failed to fetch' in result['error']


class TestFetchMultipleAthletes:
    """Tests for fetch_multiple_athletes function."""

    @pytest.mark.asyncio
    async def test_invalid_platform(self):
        """Test error handling for invalid platform."""
        with pytest.raises(ValueError, match="Unknown platform"):
            await fetch_multiple_athletes(["123"], platform="invalid")

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """Test with empty athlete list."""
        with aioresponses():
            result = await fetch_multiple_athletes([], platform="parkrun")
            assert result == []

    @pytest.mark.asyncio
    async def test_parkrun_platform(self):
        """Test fetching multiple parkrun athletes."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/111/all/",
                body=SAMPLE_PARKRUN_HTML,
                status=200
            )
            mocked.get(
                "https://www.parkrun.org.uk/parkrunner/222/all/",
                body=SAMPLE_PARKRUN_HTML,
                status=200
            )
            results = await fetch_multiple_athletes(["111", "222"], platform="parkrun")
            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_po10_platform(self):
        """Test fetching multiple PO10 athletes."""
        with aioresponses() as mocked:
            mocked.get(
                "https://www.thepowerof10.info/athletes/profile.aspx?athleteid=111",
                body=SAMPLE_PO10_HTML,
                status=200
            )
            mocked.get(
                "https://www.thepowerof10.info/athletes/profile.aspx?athleteid=222",
                body=SAMPLE_PO10_HTML,
                status=200
            )
            results = await fetch_multiple_athletes(["111", "222"], platform="po10")
            assert len(results) == 2


class TestRunAsync:
    """Tests for run_async helper function."""

    def test_run_simple_coroutine(self):
        """Test running a simple coroutine."""
        async def simple_coro():
            return 42

        result = run_async(simple_coro())
        assert result == 42

    def test_run_async_with_exception(self):
        """Test run_async propagates exceptions."""
        async def failing_coro():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_async(failing_coro())


class TestScraperAPIIntegration:
    """Tests for ScraperAPI integration."""

    @pytest.mark.asyncio
    async def test_scraper_api_url_encoding(self):
        """Test that URLs are properly encoded for ScraperAPI."""
        with patch.dict(os.environ, {'SCRAPER_API_KEY': 'test_key'}):
            scraper = AsyncParkrunScraper()
            url = scraper._get_url("https://www.parkrun.org.uk/parkrunner/123456/all/")
            # Check URL encoding
            assert "api_key=test_key" in url
            assert "render=false" in url
            # URL should be encoded
            assert "%3A%2F%2F" in url  # :// encoded

    @pytest.mark.asyncio
    async def test_fetch_via_scraper_api(self):
        """Test fetching via ScraperAPI."""
        with patch.dict(os.environ, {'SCRAPER_API_KEY': 'test_key'}):
            with aioresponses() as mocked:
                # Mock the ScraperAPI URL
                mocked.get(
                    "http://api.scraperapi.com?api_key=test_key&url=https%3A%2F%2Fwww.parkrun.org.uk%2Fparkrunner%2F123456%2Fall%2F&render=false",
                    body=SAMPLE_PARKRUN_HTML,
                    status=200
                )
                async with AsyncParkrunScraper() as scraper:
                    result = await scraper.get_athlete_results("123456")
                    assert result['error'] is None
                    assert result['name'] == "John Smith"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_malformed_html(self):
        """Test handling of malformed HTML."""
        malformed_html = "<html><body><h2>Test</h2><table id='results'></table>"
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(malformed_html, "123456")
        # Should handle gracefully - either returns 0 runs or an error
        assert result.get('total_runs', 0) == 0 or result.get('error') is not None

    @pytest.mark.asyncio
    async def test_unicode_athlete_name(self):
        """Test handling of unicode in athlete name."""
        unicode_html = """
        <html><body>
        <h2>José García - All Results</h2>
        <table id="results">
            <tr><th>Event</th><th>Run Date</th><th>Run Number</th><th>Position</th><th>Time</th></tr>
            <tr><td>parkrun</td><td>01/01/2026</td><td>1</td><td>1</td><td>20:00</td></tr>
        </table>
        </body></html>
        """
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(unicode_html, "123456")
        assert "José García" in result['name']

    @pytest.mark.asyncio
    async def test_very_long_results_table(self):
        """Test handling of large results table."""
        rows = "\n".join([
            f"<tr><td>Event{i}</td><td>01/01/2026</td><td>{i}</td><td>{i}</td><td>25:00</td></tr>"
            for i in range(500)
        ])
        large_html = f"""
        <html><body>
        <h2>Test Athlete - All Results</h2>
        <table id="results">
            <tr><th>Event</th><th>Run Date</th><th>Run Number</th><th>Position</th><th>Time</th></tr>
            {rows}
        </table>
        </body></html>
        """
        scraper = AsyncParkrunScraper()
        result = scraper._parse_athlete_page(large_html, "123456")
        assert result['total_runs'] == 500
