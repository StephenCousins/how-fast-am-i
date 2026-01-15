"""
Athlinks results scraper using requests and BeautifulSoup.
Scrapes athlete race results from their public Athlinks profile.
Uses ScraperAPI with JavaScript rendering since Athlinks is a SPA.
"""

import logging
import os
import re
import json
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, List
from urllib.parse import quote

from utils import parse_time_to_seconds, seconds_to_time_str

logger = logging.getLogger(__name__)


class AthlinksScraper:
    """Scrapes Athlinks athlete data from their public profile."""

    BASE_URL = "https://www.athlinks.com/athletes"
    SCRAPER_API_URL = "http://api.scraperapi.com"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    # Distance categories for grouping results
    DISTANCE_CATEGORIES = {
        '5k': {'min': 4.8, 'max': 5.2, 'name': '5K'},
        '10k': {'min': 9.5, 'max': 10.5, 'name': '10K'},
        'half': {'min': 20.5, 'max': 21.5, 'name': 'Half Marathon'},
        'marathon': {'min': 41.5, 'max': 42.5, 'name': 'Marathon'},
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.scraper_api_key = os.environ.get('SCRAPER_API_KEY')
        if self.scraper_api_key:
            logger.info("ScraperAPI enabled for Athlinks scraping (with JS rendering)")

    def _get_url(self, target_url: str, render_js: bool = True) -> str:
        """Get the URL to fetch - either direct or via ScraperAPI with JS rendering."""
        if self.scraper_api_key:
            encoded_url = quote(target_url, safe='')
            render_param = "&render=true" if render_js else ""
            return f"{self.SCRAPER_API_URL}?api_key={self.scraper_api_key}&url={encoded_url}{render_param}&wait_for_selector=.race-result"
        return target_url

    def _parse_distance_km(self, distance_str: str) -> Optional[float]:
        """Parse distance string to kilometers."""
        if not distance_str:
            return None

        distance_str = distance_str.lower().strip()

        # Common patterns
        patterns = [
            (r'marathon', 42.195),
            (r'half\s*marathon', 21.0975),
            (r'(\d+(?:\.\d+)?)\s*k(?:m)?', lambda m: float(m.group(1))),
            (r'(\d+(?:\.\d+)?)\s*mi(?:le)?s?', lambda m: float(m.group(1)) * 1.60934),
            (r'5k', 5.0),
            (r'10k', 10.0),
        ]

        for pattern, converter in patterns:
            match = re.search(pattern, distance_str)
            if match:
                if callable(converter):
                    return converter(match)
                return converter

        return None

    def _categorize_distance(self, distance_km: float) -> Optional[str]:
        """Categorize a distance into standard race categories."""
        for key, cat in self.DISTANCE_CATEGORIES.items():
            if cat['min'] <= distance_km <= cat['max']:
                return key
        return None

    def get_athlete_results(self, athlete_id: str) -> Optional[Dict]:
        """
        Fetch and parse results for an Athlinks athlete.

        Args:
            athlete_id: The Athlinks athlete ID

        Returns:
            Dictionary with athlete info and race results, or None if failed
        """
        url = f"{self.BASE_URL}/{athlete_id}"
        fetch_url = self._get_url(url)

        try:
            response = self.session.get(fetch_url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.warning(f"Request failed: {e}")
            return None

        html = response.text

        # Check for common error indicators
        if "athlete not found" in html.lower() or "page not found" in html.lower():
            return None

        soup = BeautifulSoup(html, 'html.parser')

        # Try to extract data from the rendered page
        return self._parse_athlete_page(soup, athlete_id, html)

    def _parse_athlete_page(self, soup: BeautifulSoup, athlete_id: str, html: str) -> Optional[Dict]:
        """Parse the athlete profile page to extract results."""

        results = {
            'athlete_id': athlete_id,
            'name': None,
            'total_races': 0,
            'results': [],
            'pbs': {},  # Personal bests by distance
            'stats': {}
        }

        # Try to find athlete name - various possible selectors
        name_selectors = [
            'h1.athlete-name',
            '.athlete-name',
            '.profile-name',
            'h1',
            '[data-testid="athlete-name"]',
        ]

        for selector in name_selectors:
            name_elem = soup.select_one(selector)
            if name_elem and name_elem.text.strip():
                results['name'] = name_elem.text.strip()
                break

        # Try to find race results - various possible selectors
        race_selectors = [
            '.race-result',
            '.result-row',
            '.race-item',
            '[data-testid="race-result"]',
            'tr.result',
            '.event-result',
        ]

        race_elements = []
        for selector in race_selectors:
            race_elements = soup.select(selector)
            if race_elements:
                break

        # Parse each race result
        for race_elem in race_elements:
            race_data = self._parse_race_element(race_elem)
            if race_data:
                results['results'].append(race_data)

        # If we couldn't find structured elements, try to extract from JSON in page
        if not results['results']:
            results = self._try_extract_from_json(html, athlete_id) or results

        # Calculate stats if we have results
        if results['results']:
            results['total_races'] = len(results['results'])
            results['stats'] = self._calculate_stats(results['results'])
            results['pbs'] = self._get_personal_bests(results['results'])

        # If we still don't have a name, use a placeholder
        if not results['name']:
            results['name'] = f"Athlete {athlete_id}"

        return results

    def _parse_race_element(self, elem) -> Optional[Dict]:
        """Parse a single race result element."""
        race = {
            'event_name': None,
            'date': None,
            'distance': None,
            'distance_km': None,
            'time': None,
            'time_seconds': None,
            'pace': None,
            'place': None,
            'age_group_place': None,
        }

        # Try various selectors for each field
        text_content = elem.get_text(' ', strip=True)

        # Event name
        name_elem = elem.select_one('.event-name, .race-name, .event-title, a[href*="event"]')
        if name_elem:
            race['event_name'] = name_elem.text.strip()

        # Date
        date_elem = elem.select_one('.date, .race-date, .event-date, time')
        if date_elem:
            race['date'] = date_elem.text.strip()

        # Time
        time_elem = elem.select_one('.time, .finish-time, .result-time')
        if time_elem:
            race['time'] = time_elem.text.strip()
            race['time_seconds'] = parse_time_to_seconds(race['time'])

        # Distance
        distance_elem = elem.select_one('.distance, .race-distance')
        if distance_elem:
            race['distance'] = distance_elem.text.strip()
            race['distance_km'] = self._parse_distance_km(race['distance'])

        # Only return if we have at least some data
        if race['event_name'] or race['time']:
            return race

        return None

    def _try_extract_from_json(self, html: str, athlete_id: str) -> Optional[Dict]:
        """Try to extract athlete data from embedded JSON in the page."""

        # Look for JSON data in script tags or data attributes
        patterns = [
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__PRELOADED_STATE__\s*=\s*({.*?});',
            r'"athlete":\s*({.*?})',
            r'"races":\s*(\[.*?\])',
        ]

        for pattern in patterns:
            match = re.search(pattern, html, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                    # Process the JSON data if found
                    return self._process_json_data(data, athlete_id)
                except json.JSONDecodeError:
                    continue

        return None

    def _process_json_data(self, data: Dict, athlete_id: str) -> Optional[Dict]:
        """Process JSON data extracted from the page."""
        results = {
            'athlete_id': athlete_id,
            'name': data.get('name') or data.get('displayName') or f"Athlete {athlete_id}",
            'total_races': 0,
            'results': [],
            'pbs': {},
            'stats': {}
        }

        # Try to find races in various possible locations
        races = data.get('races') or data.get('results') or data.get('entries') or []

        if isinstance(races, list):
            for race in races:
                race_data = {
                    'event_name': race.get('eventName') or race.get('name') or race.get('raceName'),
                    'date': race.get('date') or race.get('eventDate'),
                    'distance': race.get('distance'),
                    'distance_km': race.get('distanceKm'),
                    'time': race.get('time') or race.get('finishTime'),
                    'time_seconds': race.get('timeSeconds') or parse_time_to_seconds(race.get('time', '')),
                    'pace': race.get('pace'),
                    'place': race.get('place') or race.get('overallPlace'),
                    'age_group_place': race.get('ageGroupPlace') or race.get('divisionPlace'),
                }

                if race_data['event_name'] or race_data['time']:
                    results['results'].append(race_data)

        results['total_races'] = len(results['results'])
        return results

    def _calculate_stats(self, races: List[Dict]) -> Dict:
        """Calculate summary statistics from race results."""
        stats = {
            'total_races': len(races),
            'total_distance_km': 0,
            'total_time_seconds': 0,
        }

        distances_with_times = []

        for race in races:
            if race.get('distance_km'):
                stats['total_distance_km'] += race['distance_km']
            if race.get('time_seconds'):
                stats['total_time_seconds'] += race['time_seconds']
                if race.get('distance_km'):
                    distances_with_times.append(race)

        stats['total_distance_miles'] = round(stats['total_distance_km'] * 0.621371, 1)

        return stats

    def _get_personal_bests(self, races: List[Dict]) -> Dict:
        """Extract personal best times by distance category."""
        pbs = {}

        for race in races:
            if not race.get('time_seconds') or not race.get('distance_km'):
                continue

            category = self._categorize_distance(race['distance_km'])
            if not category:
                continue

            if category not in pbs or race['time_seconds'] < pbs[category]['time_seconds']:
                pbs[category] = {
                    'time': race['time'],
                    'time_seconds': race['time_seconds'],
                    'event': race.get('event_name', 'Unknown'),
                    'date': race.get('date', 'Unknown'),
                    'distance_name': self.DISTANCE_CATEGORIES[category]['name'],
                }

        return pbs


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = AthlinksScraper()

    # Test with a sample athlete ID
    test_id = "319145186"
    logger.info(f"Testing Athlinks scraper with athlete ID: {test_id}")

    results = scraper.get_athlete_results(test_id)
    if results:
        logger.info(f"Athlete: {results['name']}")
        logger.info(f"Total races: {results['total_races']}")
        logger.info("Personal Bests:")
        for dist, pb in results.get('pbs', {}).items():
            logger.info(f"  {pb['distance_name']}: {pb['time']} at {pb['event']}")
        logger.info("Recent results:")
        for race in results['results'][:5]:
            logger.info(f"  {race.get('event_name', 'Unknown')}: {race.get('time', 'N/A')}")
    else:
        logger.info("Failed to fetch results")
