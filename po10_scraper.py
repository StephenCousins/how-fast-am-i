"""
Power of 10 scraper for UK athletics results.
Extracts athlete PBs across multiple distances.
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Optional
import re

from utils import parse_time_to_seconds, seconds_to_time_str

logger = logging.getLogger(__name__)


class PowerOf10Scraper:
    """Scrapes athlete data from Power of 10 (thepowerof10.info)."""

    BASE_URL = "https://www.thepowerof10.info/athletes/profile.aspx"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
    }

    # Standard distance mappings
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
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def get_athlete_by_id(self, athlete_id: str) -> dict:
        """
        Fetch athlete data by Power of 10 athlete ID.

        Returns dict with:
            - name: Athlete name
            - club: Running club
            - age_group: Age category (e.g., V50, SEN)
            - pbs: Dict of personal bests by distance
            - error: Error message if failed
        """
        url = f"{self.BASE_URL}?athleteid={athlete_id}"

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            return {
                'error': f'Failed to fetch data: {str(e)}',
                'athlete_id': athlete_id
            }

        return self._parse_athlete_page(response.text, athlete_id)

    def search_athlete(self, name: str) -> list:
        """
        Search for athletes by name.
        Returns list of matching athletes with their IDs.
        """
        search_url = "https://www.thepowerof10.info/athletes/athleteslookup.aspx"
        params = {'surname': name.split()[-1] if ' ' in name else name}

        try:
            response = self.session.get(search_url, params=params, timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        # Find athlete links
        for link in soup.find_all('a', href=re.compile(r'profile\.aspx\?athleteid=\d+')):
            match = re.search(r'athleteid=(\d+)', link.get('href', ''))
            if match:
                results.append({
                    'name': link.get_text(strip=True),
                    'athlete_id': match.group(1)
                })

        return results[:10]  # Limit to 10 results

    def _parse_athlete_page(self, html: str, athlete_id: str) -> dict:
        """Parse the athlete profile page."""
        soup = BeautifulSoup(html, 'html.parser')

        # Get athlete name
        name = "Unknown"
        h2 = soup.find('h2')
        if h2:
            name = h2.get_text(strip=True)

        # Get club and other info - data is in combined strings
        club = None
        age_group = None
        gender = None

        # Look for the info block containing Club:, Gender:, Age Group:
        page_text = soup.get_text()

        # Use lookahead to stop at next field
        club_match = re.search(r'Club:([A-Za-z0-9 ]+?)(?:Gender:|County:|$)', page_text)
        if club_match:
            club = club_match.group(1).strip()

        gender_match = re.search(r'Gender:(Male|Female)', page_text)
        if gender_match:
            gender = gender_match.group(1)

        age_group_match = re.search(r'Age Group:(V?\d+|SEN|U\d+)', page_text)
        if age_group_match:
            age_group = age_group_match.group(1)

        # Extract PBs - look for rows with known event codes
        pbs = {}
        target_events = ['5K', '10K', '10M', 'HM', 'Mar', '5000', '10000', '20M']

        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                event = cells[0].get_text(strip=True)
                if event in target_events:
                    pb_text = cells[1].get_text(strip=True)
                    pb_seconds = parse_time_to_seconds(pb_text)

                    if pb_seconds:
                        # Normalize event name
                        normalized_event = self.DISTANCE_MAP.get(event, event)

                        # Only keep if it's better than existing (shouldn't happen, but safety check)
                        if normalized_event not in pbs or pb_seconds < pbs[normalized_event]['seconds']:
                            pbs[normalized_event] = {
                                'time': pb_text,
                                'seconds': pb_seconds,
                                'time_formatted': seconds_to_time_str(pb_seconds)
                            }

        return {
            'name': name,
            'athlete_id': athlete_id,
            'club': club,
            'age_group': age_group,
            'gender': gender.lower() if gender else None,
            'pbs': pbs,
            'error': None
        }


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = PowerOf10Scraper()
    result = scraper.get_athlete_by_id("434569")

    logger.info(f"Name: {result.get('name')}")
    logger.info(f"Club: {result.get('club')}")
    logger.info(f"Age Group: {result.get('age_group')}")
    logger.info("Personal Bests:")
    for event, pb in result.get('pbs', {}).items():
        logger.info(f"  {event}: {pb['time_formatted']}")
