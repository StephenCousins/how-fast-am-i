"""
Async scraper support using aiohttp.

Provides async wrappers for the existing scrapers to enable non-blocking
scraping operations. Useful for handling multiple concurrent requests
without blocking the main thread.

Usage:
    from async_scraper import AsyncParkrunScraper, AsyncPowerOf10Scraper

    async def main():
        async with AsyncParkrunScraper() as scraper:
            result = await scraper.get_athlete_results("123456")

    asyncio.run(main())
"""

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import quote

import aiohttp
from bs4 import BeautifulSoup

from utils import parse_time_to_seconds, seconds_to_time_str

logger = logging.getLogger(__name__)


class AsyncParkrunScraper:
    """Async version of ParkrunScraper using aiohttp."""

    BASE_URL = "https://www.parkrun.org.uk/parkrunner"
    SCRAPER_API_URL = "http://api.scraperapi.com"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
    }

    def __init__(self):
        self.scraper_api_key = os.environ.get('SCRAPER_API_KEY')
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            self._session = aiohttp.ClientSession(
                headers=self.HEADERS,
                timeout=timeout
            )

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_url(self, target_url: str) -> str:
        """Get the URL to fetch - either direct or via ScraperAPI."""
        if self.scraper_api_key:
            encoded_url = quote(target_url, safe='')
            return f"{self.SCRAPER_API_URL}?api_key={self.scraper_api_key}&url={encoded_url}&render=false"
        return target_url

    async def get_athlete_results(self, athlete_id: str) -> dict:
        """
        Fetch and parse results for a given parkrun athlete ID (async).

        Returns dict with:
            - name: Athlete name
            - athlete_id: The ID
            - total_runs: Number of parkruns completed
            - results: List of individual run results
            - stats: Calculated statistics (avg, best, etc.)
            - error: Error message if scraping failed
        """
        await self._ensure_session()
        target_url = f"{self.BASE_URL}/{athlete_id}/all/"

        try:
            fetch_url = self._get_url(target_url)
            async with self._session.get(fetch_url) as response:
                if response.status == 403:
                    return {
                        'error': 'Access denied by parkrun. Please try again later.',
                        'athlete_id': athlete_id
                    }

                if response.status == 404:
                    return {
                        'error': f'Athlete ID {athlete_id} not found.',
                        'athlete_id': athlete_id
                    }

                response.raise_for_status()
                html = await response.text()

        except aiohttp.ClientError as e:
            return {
                'error': f'Failed to fetch data: {str(e)}',
                'athlete_id': athlete_id
            }
        except asyncio.TimeoutError:
            return {
                'error': 'Request timed out. Please try again.',
                'athlete_id': athlete_id
            }

        return self._parse_athlete_page(html, athlete_id)

    def _parse_athlete_page(self, html: str, athlete_id: str) -> dict:
        """Parse the athlete results page HTML."""
        soup = BeautifulSoup(html, 'html.parser')

        # Get athlete name
        name = "Unknown"
        name_elem = soup.find('h2')
        if name_elem:
            name = name_elem.get_text(strip=True)
            name = re.sub(r'\s*-\s*All Results.*', '', name)

        # Find the results table
        results_table = None
        tables = soup.find_all('table', {'id': 'results'})

        for table in tables:
            first_row = table.find('tr')
            if first_row:
                headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
                if 'Event' in headers and 'Time' in headers:
                    results_table = table
                    break

        if not results_table:
            results_table = soup.find('table', class_='sortable')

        if not results_table:
            return {
                'error': 'Could not find results table.',
                'athlete_id': athlete_id,
                'name': name
            }

        # Parse table rows
        results = []
        rows = results_table.find_all('tr')

        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) >= 5:
                try:
                    result = {
                        'event': cells[0].get_text(strip=True),
                        'run_date': cells[1].get_text(strip=True),
                        'run_number': cells[2].get_text(strip=True),
                        'position': cells[3].get_text(strip=True),
                        'time': cells[4].get_text(strip=True),
                        'age_grade': cells[5].get_text(strip=True) if len(cells) > 5 else None,
                        'pb': 'PB' in row.get_text() or 'New PB!' in row.get_text()
                    }
                    result['time_seconds'] = parse_time_to_seconds(result['time'])
                    if result['time_seconds']:
                        results.append(result)
                except (IndexError, AttributeError):
                    continue

        # Import stats calculation from sync scraper
        from scraper import ParkrunScraper
        sync_scraper = ParkrunScraper()
        stats = sync_scraper._calculate_stats(results)

        return {
            'name': name,
            'athlete_id': athlete_id,
            'total_runs': len(results),
            'results': results,
            'stats': stats,
            'error': None
        }


class AsyncPowerOf10Scraper:
    """Async version of PowerOf10Scraper using aiohttp."""

    BASE_URL = "https://www.thepowerof10.info/athletes/profile.aspx"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
    }

    DISTANCE_MAP = {
        '5K': '5K',
        '5000': '5K',
        '10K': '10K',
        '10000': '10K',
        '10M': '10M',
        'HM': 'Half Marathon',
        'Mar': 'Marathon',
        '20M': '20 Miles',
    }

    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                headers=self.HEADERS,
                timeout=timeout
            )

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_athlete_by_id(self, athlete_id: str) -> dict:
        """
        Fetch athlete data by Power of 10 athlete ID (async).

        Returns dict with:
            - name: Athlete name
            - club: Running club
            - age_group: Age category
            - pbs: Dict of personal bests by distance
            - error: Error message if failed
        """
        await self._ensure_session()
        url = f"{self.BASE_URL}?athleteid={athlete_id}"

        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html = await response.text()
        except aiohttp.ClientError as e:
            return {
                'error': f'Failed to fetch data: {str(e)}',
                'athlete_id': athlete_id
            }
        except asyncio.TimeoutError:
            return {
                'error': 'Request timed out. Please try again.',
                'athlete_id': athlete_id
            }

        # Use sync scraper for parsing
        from po10_scraper import PowerOf10Scraper
        sync_scraper = PowerOf10Scraper()
        return sync_scraper._parse_athlete_page(html, athlete_id)


async def fetch_multiple_athletes(athlete_ids: list, platform: str = 'parkrun') -> list:
    """
    Fetch multiple athletes concurrently.

    Args:
        athlete_ids: List of athlete IDs to fetch
        platform: 'parkrun' or 'po10'

    Returns:
        List of results in the same order as athlete_ids
    """
    if platform == 'parkrun':
        async with AsyncParkrunScraper() as scraper:
            tasks = [scraper.get_athlete_results(aid) for aid in athlete_ids]
            return await asyncio.gather(*tasks, return_exceptions=True)
    elif platform == 'po10':
        async with AsyncPowerOf10Scraper() as scraper:
            tasks = [scraper.get_athlete_by_id(aid) for aid in athlete_ids]
            return await asyncio.gather(*tasks, return_exceptions=True)
    else:
        raise ValueError(f"Unknown platform: {platform}")


def run_async(coro):
    """
    Helper to run async code from sync context.

    Usage:
        result = run_async(async_scraper.get_athlete_results("123456"))
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, create a task
            return asyncio.ensure_future(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create a new one
        return asyncio.run(coro)


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def test_async_scrapers():
        # Test async parkrun scraper
        async with AsyncParkrunScraper() as scraper:
            result = await scraper.get_athlete_results("123456")
            logger.info(f"Parkrun result: {result.get('name', result.get('error'))}")

        # Test async PO10 scraper
        async with AsyncPowerOf10Scraper() as scraper:
            result = await scraper.get_athlete_by_id("434569")
            logger.info(f"PO10 result: {result.get('name', result.get('error'))}")

        # Test concurrent fetching
        logger.info("Testing concurrent fetch...")
        results = await fetch_multiple_athletes(["123456", "654321"], "parkrun")
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Error: {r}")
            else:
                logger.info(f"Got: {r.get('name', r.get('error'))}")

    asyncio.run(test_async_scrapers())
