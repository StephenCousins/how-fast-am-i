# How Fast Am I? - Parkrun Comparison Tool

[![Tests](https://github.com/StephenCousins/how-fast-am-i/actions/workflows/tests.yml/badge.svg)](https://github.com/StephenCousins/how-fast-am-i/actions/workflows/tests.yml)

A Flask web application that scrapes and compares running times from multiple platforms, providing percentile rankings, age grading, and trend analysis.

## Features

- **Multi-Platform Support**
  - Parkrun (UK/Global) - 5K parkrun results
  - Power of 10 (UK) - Multi-distance track & road results
  - Athlinks (USA) - Multi-distance road race results

- **Performance Analysis**
  - Percentile rankings against global/UK averages
  - Age grading using 2023 WMA factors
  - Trend analysis (improving/stable/declining)
  - Outlier detection for non-typical runs

- **Smart Caching**
  - Database caching with configurable TTL (default 6 hours)
  - Stale cache fallback when scraping fails
  - Rate limiting to protect API credits

## Tech Stack

- Python 3.10+
- Flask 3.0.0
- Flask-SQLAlchemy (PostgreSQL/SQLite)
- BeautifulSoup4 (web scraping)
- Gunicorn (production server)

## Installation

### Prerequisites

- Python 3.10 or higher
- PostgreSQL (production) or SQLite (development)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/parkrun-scraper.git
   cd parkrun-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   export DATABASE_URL="sqlite:///athletes.db"  # Or PostgreSQL URL
   export SCRAPER_API_KEY="your_key"  # Optional: for bypassing IP blocks
   export REFRESH_COOLDOWN_HOURS=6  # Optional: cache TTL
   ```

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the development server:
   ```bash
   flask run
   ```

## Usage

### Web Interface

Navigate to `http://localhost:5000` and enter your athlete ID from any supported platform:

- **Parkrun**: Find your ID in your parkrun profile URL (e.g., `parkrun.org.uk/parkrunner/123456`)
- **Power of 10**: Find your ID on your athlete profile page
- **Athlinks**: Find your ID in your Athlinks profile URL

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET/POST | Parkrun analysis page |
| `/power-of-10` | GET/POST | Power of 10 analysis page |
| `/athlinks` | GET/POST | Athlinks analysis page |
| `/health` | GET | Health check endpoint |
| `/stats` | GET | Database statistics |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `DATABASE_URL` | `sqlite:///athletes.db` | Database connection string |
| `SCRAPER_API_KEY` | None | ScraperAPI key for bypassing blocks |
| `REFRESH_COOLDOWN_HOURS` | 6 | Minimum hours between cache refreshes |

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
parkrun-scraper/
├── app.py                 # Flask application and routes
├── models.py              # SQLAlchemy database models
├── scraper.py             # Parkrun scraper
├── po10_scraper.py        # Power of 10 scraper
├── athlinks_scraper.py    # Athlinks scraper
├── utils.py               # Shared utilities (time conversion, validation)
├── comparisons.py         # Percentile and comparison calculations
├── distance_comparisons.py # Multi-distance comparisons
├── age_grading.py         # WMA age grading calculations
├── templates/             # Jinja2 HTML templates
├── static/                # CSS and static assets
├── migrations/            # Database migrations (Flask-Migrate)
├── test_utils.py          # Tests for utilities
└── test_age_grading.py    # Tests for age grading
```

## Deployment

### Railway

The app is configured for Railway deployment:

```bash
# Procfile
web: gunicorn app:app --workers 2 --timeout 120
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "app:app", "--workers", "2", "--bind", "0.0.0.0:8000"]
```

## Rate Limiting

To protect ScraperAPI credits and external services:

- 200 requests per day per IP
- 50 requests per hour per IP
- 10 requests per minute for Parkrun lookups

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- [parkrun](https://www.parkrun.org.uk) - Source of parkrun data
- [Power of 10](https://www.thepowerof10.info) - UK athletics results
- [Athlinks](https://www.athlinks.com) - US race results
- [RunRepeat](https://runrepeat.com) - Global running statistics (107.9M race results)
- [WMA Age Grading](https://world-masters-athletics.com) - 2023 age grading factors
