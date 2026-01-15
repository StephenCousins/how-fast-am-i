"""
Parkrun results scraper using requests and BeautifulSoup.
Scrapes athlete results from their public parkrun profile.
Supports ScraperAPI for bypassing IP blocks on cloud servers.
"""

import logging
import os
import requests
from bs4 import BeautifulSoup
from typing import Optional
from urllib.parse import quote
import re

from utils import parse_time_to_seconds, seconds_to_time_str

logger = logging.getLogger(__name__)


class ParkrunScraper:
    """Scrapes parkrun athlete data from their public profile."""

    BASE_URL = "https://www.parkrun.org.uk/parkrunner"
    SCRAPER_API_URL = "http://api.scraperapi.com"

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.parkrun.org.uk/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Cache-Control': 'max-age=0',
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        # Check for ScraperAPI key (used on Railway to bypass IP blocks)
        self.scraper_api_key = os.environ.get('SCRAPER_API_KEY')
        if self.scraper_api_key:
            logger.info("ScraperAPI enabled for parkrun scraping")

    def _get_url(self, target_url: str) -> str:
        """Get the URL to fetch - either direct or via ScraperAPI."""
        if self.scraper_api_key:
            # Route through ScraperAPI to bypass IP blocks
            encoded_url = quote(target_url, safe='')
            return f"{self.SCRAPER_API_URL}?api_key={self.scraper_api_key}&url={encoded_url}&render=false"
        return target_url

    def get_athlete_results(self, athlete_id: str) -> dict:
        """
        Fetch and parse results for a given parkrun athlete ID.

        Returns dict with:
            - name: Athlete name
            - athlete_id: The ID
            - total_runs: Number of parkruns completed
            - results: List of individual run results
            - stats: Calculated statistics (avg, best, etc.)
            - error: Error message if scraping failed
        """
        target_url = f"{self.BASE_URL}/{athlete_id}/all/"

        try:
            if self.scraper_api_key:
                # Use ScraperAPI - no need for cookies, they handle it
                fetch_url = self._get_url(target_url)
                response = self.session.get(fetch_url, timeout=60)  # Longer timeout for proxy
            else:
                # Direct request - first visit main page for cookies
                self.session.get("https://www.parkrun.org.uk/", timeout=10)
                response = self.session.get(target_url, timeout=15)

            if response.status_code == 403:
                return {
                    'error': 'Access denied by parkrun. Please try again later.',
                    'athlete_id': athlete_id
                }

            if response.status_code == 404:
                return {
                    'error': f'Athlete ID {athlete_id} not found.',
                    'athlete_id': athlete_id
                }

            response.raise_for_status()

        except requests.RequestException as e:
            return {
                'error': f'Failed to fetch data: {str(e)}',
                'athlete_id': athlete_id
            }

        return self._parse_athlete_page(response.text, athlete_id)

    def _parse_athlete_page(self, html: str, athlete_id: str) -> dict:
        """Parse the athlete results page HTML."""
        soup = BeautifulSoup(html, 'html.parser')

        # Get athlete name
        name = "Unknown"
        name_elem = soup.find('h2')
        if name_elem:
            name = name_elem.get_text(strip=True)
            # Remove " - All Results" suffix if present
            name = re.sub(r'\s*-\s*All Results.*', '', name)

        # Find the results table - there are multiple tables with id='results'
        # We need the one with Event, Run Date, etc. headers (the detailed results)
        results_table = None
        tables = soup.find_all('table', {'id': 'results'})

        for table in tables:
            first_row = table.find('tr')
            if first_row:
                headers = [th.get_text(strip=True) for th in first_row.find_all(['th', 'td'])]
                if 'Event' in headers and 'Time' in headers:
                    results_table = table
                    break

        # Fallback to sortable table if not found
        if not results_table:
            results_table = soup.find('table', class_='sortable')

        if not results_table:
            return {
                'error': 'Could not find results table. The page structure may have changed.',
                'athlete_id': athlete_id,
                'name': name
            }

        # Parse table rows
        results = []
        rows = results_table.find_all('tr')

        for row in rows[1:]:  # Skip header row
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

                    # Parse time to seconds for calculations
                    result['time_seconds'] = parse_time_to_seconds(result['time'])

                    if result['time_seconds']:  # Only add valid results
                        results.append(result)
                except (IndexError, AttributeError):
                    continue

        # Calculate statistics
        stats = self._calculate_stats(results)

        return {
            'name': name,
            'athlete_id': athlete_id,
            'total_runs': len(results),
            'results': results,
            'stats': stats,
            'error': None
        }

    def _calculate_stats(self, results: list) -> dict:
        """Calculate statistics from results including advanced analysis."""
        if not results:
            return {}

        times = [r['time_seconds'] for r in results if r['time_seconds']]

        if not times:
            return {}

        times_sorted = sorted(times)

        avg_seconds = sum(times) / len(times)
        best_seconds = min(times)
        worst_seconds = max(times)

        # Median
        mid = len(times_sorted) // 2
        if len(times_sorted) % 2 == 0:
            median_seconds = (times_sorted[mid - 1] + times_sorted[mid]) / 2
        else:
            median_seconds = times_sorted[mid]

        # Find PB details (best time with date and event)
        pb_run = min([r for r in results if r['time_seconds']], key=lambda x: x['time_seconds'])

        # Find worst run details
        worst_run = max([r for r in results if r['time_seconds']], key=lambda x: x['time_seconds'])

        # Outlier detection: times > 1.5x median are likely walking/with kids
        outlier_threshold = median_seconds * 1.5
        outliers = [r for r in results if r['time_seconds'] and r['time_seconds'] > outlier_threshold]
        normal_runs = [r for r in results if r['time_seconds'] and r['time_seconds'] <= outlier_threshold]

        # Calculate "typical" time excluding outliers
        if normal_runs:
            normal_times = [r['time_seconds'] for r in normal_runs]
            typical_avg_seconds = sum(normal_times) / len(normal_times)
            typical_best = min(normal_times)

            # Typical median
            normal_sorted = sorted(normal_times)
            mid_n = len(normal_sorted) // 2
            if len(normal_sorted) % 2 == 0:
                typical_median = (normal_sorted[mid_n - 1] + normal_sorted[mid_n]) / 2
            else:
                typical_median = normal_sorted[mid_n]
        else:
            typical_avg_seconds = avg_seconds
            typical_median = median_seconds
            typical_best = best_seconds

        # Recent form (last 20 runs, excluding outliers)
        recent_runs = results[:20]
        recent_normal = [r for r in recent_runs if r['time_seconds'] and r['time_seconds'] <= outlier_threshold]
        recent_times = [r['time_seconds'] for r in recent_normal] if recent_normal else []
        recent_avg = sum(recent_times) / len(recent_times) if recent_times else None

        # Historical comparison (runs older than last 20, excluding outliers)
        older_runs = results[20:]
        older_normal = [r for r in older_runs if r['time_seconds'] and r['time_seconds'] <= outlier_threshold]
        older_times = [r['time_seconds'] for r in older_normal] if older_normal else []
        older_avg = sum(older_times) / len(older_times) if older_times else None

        # Trend analysis
        trend = self._calculate_trend(recent_avg, older_avg, typical_median)

        # Calculate how old the PB is
        pb_age = self._calculate_time_ago(pb_run.get('run_date', ''))

        # Age grades
        age_grades = []
        for r in results:
            if r.get('age_grade'):
                try:
                    ag = float(r['age_grade'].replace('%', ''))
                    age_grades.append(ag)
                except ValueError:
                    pass

        avg_age_grade = sum(age_grades) / len(age_grades) if age_grades else None

        # Recent age grade (from recent normal runs)
        recent_age_grades = []
        for r in recent_normal[:10]:
            if r.get('age_grade'):
                try:
                    ag = float(r['age_grade'].replace('%', ''))
                    recent_age_grades.append(ag)
                except ValueError:
                    pass
        recent_avg_age_grade = sum(recent_age_grades) / len(recent_age_grades) if recent_age_grades else None

        return {
            # Basic stats
            'average_seconds': int(avg_seconds),
            'average_time': seconds_to_time_str(int(avg_seconds)),
            'best_seconds': best_seconds,
            'best_time': seconds_to_time_str(best_seconds),
            'worst_seconds': worst_seconds,
            'worst_time': seconds_to_time_str(worst_seconds),
            'median_seconds': int(median_seconds),
            'median_time': seconds_to_time_str(int(median_seconds)),
            'total_runs': len(times),

            # PB context
            'pb_event': pb_run.get('event', 'Unknown'),
            'pb_date': pb_run.get('run_date', 'Unknown'),
            'pb_age': pb_age,

            # Worst run context
            'worst_event': worst_run.get('event', 'Unknown'),
            'worst_date': worst_run.get('run_date', 'Unknown'),

            # Outlier analysis
            'outlier_count': len(outliers),
            'normal_run_count': len(normal_runs),
            'outlier_threshold_time': seconds_to_time_str(int(outlier_threshold)),

            # Typical stats (excluding outliers)
            'typical_avg_seconds': int(typical_avg_seconds),
            'typical_avg_time': seconds_to_time_str(int(typical_avg_seconds)),
            'typical_median_seconds': int(typical_median),
            'typical_median_time': seconds_to_time_str(int(typical_median)),

            # Recent form
            'recent_run_count': len(recent_times),
            'recent_avg_seconds': int(recent_avg) if recent_avg else None,
            'recent_avg_time': seconds_to_time_str(int(recent_avg)) if recent_avg else None,

            # Historical comparison
            'older_avg_seconds': int(older_avg) if older_avg else None,
            'older_avg_time': seconds_to_time_str(int(older_avg)) if older_avg else None,

            # Trend
            'trend': trend['direction'],
            'trend_message': trend['message'],
            'trend_diff_seconds': trend['diff_seconds'],
            'trend_diff_time': trend['diff_time'],

            # Age grades
            'avg_age_grade': round(avg_age_grade, 1) if avg_age_grade else None,
            'recent_avg_age_grade': round(recent_avg_age_grade, 1) if recent_avg_age_grade else None,
        }

    def _calculate_trend(self, recent_avg: float, older_avg: float, median: float) -> dict:
        """Analyze trend: improving, declining, or stable."""
        if not recent_avg or not older_avg:
            return {
                'direction': 'unknown',
                'message': 'Not enough data to determine trend',
                'diff_seconds': 0,
                'diff_time': '0:00'
            }

        diff = older_avg - recent_avg  # Positive = getting faster

        # Use 2% of median as threshold for "significant" change
        threshold = median * 0.02

        if diff > threshold:
            direction = 'improving'
            message = f"Getting faster! Recent runs are {seconds_to_time_str(int(abs(diff)))} quicker than your historical average"
        elif diff < -threshold:
            direction = 'declining'
            message = f"Recent runs are {seconds_to_time_str(int(abs(diff)))} slower than your historical average"
        else:
            direction = 'stable'
            message = "Your pace is consistent - maintaining steady performance"

        return {
            'direction': direction,
            'message': message,
            'diff_seconds': int(diff),
            'diff_time': seconds_to_time_str(int(abs(diff)))
        }

    def _calculate_time_ago(self, date_str: str) -> str:
        """Calculate how long ago a date was."""
        if not date_str:
            return 'Unknown'

        try:
            from datetime import datetime

            # parkrun dates are typically in DD/MM/YYYY format
            run_date = datetime.strptime(date_str, '%d/%m/%Y')
            today = datetime.now()
            diff = today - run_date

            years = diff.days // 365
            months = (diff.days % 365) // 30

            if years > 0:
                if months > 0:
                    return f"{years} year{'s' if years > 1 else ''}, {months} month{'s' if months > 1 else ''} ago"
                return f"{years} year{'s' if years > 1 else ''} ago"
            elif months > 0:
                return f"{months} month{'s' if months > 1 else ''} ago"
            elif diff.days > 0:
                return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
            else:
                return "Today"
        except (ValueError, TypeError):
            return date_str


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = ParkrunScraper()
    # Test with a sample ID
    result = scraper.get_athlete_results("123456")
    logger.info(result)
