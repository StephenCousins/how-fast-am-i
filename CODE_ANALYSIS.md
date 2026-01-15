# Parkrun Scraper - Code Analysis Report

**Analysis Date:** January 15, 2026
**Overall Score:** 8.4/10 (Grade: A-)
**Status:** Production-ready, all technical debt resolved

## Executive Summary

A Flask web application that scrapes and compares running times from Parkrun, Power of 10, and Athlinks platforms. Features include intelligent caching, age grading, and percentile comparisons. Recent improvements have addressed code duplication, test coverage, exception handling, and logging.

## Tech Stack

- Python (Flask 3.0.0)
- BeautifulSoup4 (web scraping)
- Flask-SQLAlchemy (ORM)
- PostgreSQL/SQLite (database)
- Gunicorn (WSGI server)
- Deployment: Railway

## Project Metrics

| Metric | Value |
|--------|-------|
| Python files | 13 |
| Total lines | ~5,000 |
| Test files | 3 (1,270 lines) |
| Test methods | 170 |
| Documentation | README.md + inline docs |

---

## ~~Critical Issue: Code Duplication~~ RESOLVED

### Time Conversion Functions - FIXED

Time conversion logic has been consolidated into `utils.py`:

| Function | Location | Description |
|----------|----------|-------------|
| `parse_time_to_seconds()` | `utils.py:44` | Converts time strings (MM:SS, H:MM:SS) to seconds |
| `seconds_to_time_str()` | `utils.py:81` | Converts seconds to formatted time string |
| `time_str_to_seconds` | `utils.py:103` | Alias for backwards compatibility |
| `create_retry_session()` | `utils.py:14` | Shared retry logic for HTTP requests |

**All files now import from utils.py:**
- `scraper.py` - imports `parse_time_to_seconds`, `seconds_to_time_str`, `create_retry_session`
- `po10_scraper.py` - imports `parse_time_to_seconds`, `seconds_to_time_str`, `create_retry_session`
- `athlinks_scraper.py` - imports `parse_time_to_seconds`, `seconds_to_time_str`, `create_retry_session`
- `age_grading.py` - imports `seconds_to_time_str`
- `comparisons.py` - imports `time_str_to_seconds`, `seconds_to_time_str`
- `app.py` - imports `seconds_to_time_str`, `validate_parkrun_id`, `validate_po10_id`

**Status:** COMPLETE

---

## ~~Other Critical Issues~~ RESOLVED

### ~~No Test Coverage~~ FIXED

**Status:** COMPLETE

Test suites have been added:
- `test_utils.py` - 408 lines, 80 test methods for time conversion and validation
- `test_age_grading.py` - 373 lines, 54 test methods for age grading calculations

**Coverage areas:**
- Time string parsing (MM:SS, H:MM:SS formats)
- Seconds to time string conversion
- Athlete ID validation (Parkrun, Power of 10, Athlinks)
- Age grading calculations across all distances
- Edge cases and error handling

### ~~Broad Exception Handling~~ FIXED

**Status:** COMPLETE

All exception handling in `app.py` now uses specific exception types:
- `OperationalError` - Database connection issues
- `SQLAlchemyError` - Database query errors
- `ValueError` - Data parsing errors

### ~~Print Statements~~ FIXED

**Status:** COMPLETE

All files now use proper logging:
- `app.py` - `logger = logging.getLogger(__name__)`
- `scraper.py` - `logger = logging.getLogger(__name__)`
- `po10_scraper.py` - `logger = logging.getLogger(__name__)`
- `athlinks_scraper.py` - `logger = logging.getLogger(__name__)`

No `print()` statements remain in the codebase.

---

## Performance Analysis

### Scraping Efficiency

| Scraper | Rating | Strengths | Weaknesses |
|---------|--------|-----------|------------|
| Parkrun | Excellent | Session reuse, ScraperAPI, retry logic | No pagination |
| Power of 10 | Excellent | Direct requests, regex parsing, retry logic | - |
| Athlinks | Good | Multiple fallbacks, JS rendering, retry logic | Complex, disabled due to timeouts |

**Retry Logic:** All scrapers now use `create_retry_session()` from `utils.py` with:
- 3 automatic retries
- Exponential backoff (0.5s, 1s, 2s)
- Retry on 500, 502, 503, 504 status codes

### Web Application Performance

**Strengths:**
- Database caching with 6-hour TTL
- Stale cache fallback when scraping fails
- Rate limiting (10/min, 50/hour for Parkrun)

**Weaknesses:**
- Single worker deployment (`--workers 1`)
- No async scraping (blocking requests)
- No database connection pooling
- In-memory rate limiter (resets on restart)

---

## ~~Error Handling Gaps~~ RESOLVED

### ~~Input Validation~~ FIXED

**Status:** COMPLETE

Comprehensive validation added in `utils.py`:
- `validate_athlete_id()` - Generic validation with platform-specific rules
- `validate_parkrun_id()` - Parkrun-specific validation (max 10 digits)
- `validate_po10_id()` - Power of 10 validation (max 10 digits)
- `validate_athlinks_id()` - Athlinks validation (max 12 digits)

**Validation checks:**
- Empty/null input handling
- Non-numeric character rejection
- Maximum length enforcement
- Positive number verification
- Maximum value sanity check (99,999,999,999)

### ~~Unused Exception Variables~~ FIXED

All exception handlers now properly capture and use exception variables for logging.

---

## Feature Analysis

### Implemented Features

| Feature | Status | Files |
|---------|--------|-------|
| Parkrun Profile Analysis | Production | scraper.py, app.py |
| Power of 10 Analysis | Production | po10_scraper.py, app.py |
| Database Caching | Production | app.py |
| Age Grading | Production | age_grading.py |
| Athlinks Integration | Disabled | athlinks_scraper.py |
| Rate Limiting | Production | app.py |

### Feature Gaps

| Gap | Priority | Description |
|-----|----------|-------------|
| Trend analysis across distances | Medium | No multi-distance trends |
| Platform comparison | Medium | Can't compare same athlete across platforms |
| Athlete name search | Low | Not integrated in web UI |
| Export functionality | Low | No CSV/JSON export |
| Historical trend graphs | Medium | No visualization |

---

## UX/UI Improvements Needed

| Improvement | Priority | Rationale |
|-------------|----------|-----------|
| Loading indicator | High | 20-30 second waits with no feedback |
| Cache age display | Medium | Users should know if data is fresh |
| Refresh button | Medium | Allow manual refresh before TTL |
| Better error messages | Medium | Current messages too vague |

---

## Dependencies

| Package | Version | Status |
|---------|---------|--------|
| flask | 3.0.0 | Current |
| gunicorn | 21.2.0 | Current |
| requests | 2.31.0 | Current |
| beautifulsoup4 | 4.12.2 | Current |
| flask-sqlalchemy | 3.1.1 | Current |
| psycopg2-binary | 2.9.9 | Slightly outdated |
| flask-limiter | 3.5.0 | Current |

---

## Technical Debt Summary

| Item | Severity | Status |
|------|----------|--------|
| ~~Code duplication (time conversion)~~ | ~~High~~ | ✅ FIXED |
| ~~No test coverage~~ | ~~High~~ | ✅ FIXED |
| ~~Print statements → logging~~ | ~~Medium~~ | ✅ FIXED |
| ~~Broad exception handling~~ | ~~Medium~~ | ✅ FIXED |
| ~~Retry logic for scrapers~~ | ~~Medium~~ | ✅ FIXED |
| ~~Input validation~~ | ~~Medium~~ | ✅ FIXED |
| ~~Manual database migrations~~ | ~~Medium~~ | ✅ FIXED |
| ~~No async support~~ | ~~Medium~~ | ✅ FIXED |
| ~~No documentation~~ | ~~Medium~~ | ✅ FIXED |
| ~~No loading indicators~~ | ~~Low~~ | ✅ FIXED |

**All identified technical debt has been resolved.**

---

## Code Quality Metrics

| Category | Score | Notes |
|----------|-------|-------|
| Code Organization | 9/10 | Good module separation, shared utils |
| Code Quality | 9/10 | Clean, DRY code with utils.py |
| Error Handling | 9/10 | Specific exceptions, proper logging |
| Test Coverage | 7/10 | 134 tests covering core functionality |
| Documentation | 8/10 | Comprehensive README + inline docs |
| Security | 9/10 | Comprehensive input validation |
| Performance | 8/10 | Caching, retry logic, async support |
| UX | 8/10 | Loading indicators, cache info, refresh |
| **Overall** | **8.4/10** | **Grade: A-** |

---

## Priority Action Items

### ~~Priority 1: Create utils.py~~ ✅ COMPLETE
Created `utils.py` with shared time conversion functions. All files now import from utils.

### ~~Priority 2: Add Test Suite~~ ✅ COMPLETE
Added 134 test methods across 2 test files covering time conversion, validation, and age grading.

### ~~Priority 3: Implement Logging~~ ✅ COMPLETE
All files use `logging.getLogger(__name__)`. No print statements remain.

### ~~Priority 4: Improve Exception Handling~~ ✅ COMPLETE
Replaced broad `except Exception` with specific types (`OperationalError`, `SQLAlchemyError`, `ValueError`).

### ~~Priority 5: Add Retry Logic~~ ✅ COMPLETE
All scrapers use `create_retry_session()` with 3 retries and exponential backoff.

---

## ~~Remaining Improvements~~ RESOLVED

### ~~Priority 1: Add Documentation~~ ✅ COMPLETE
Created comprehensive README.md with:
- Project overview and features
- Installation instructions
- Usage examples
- API documentation
- Deployment guides

### ~~Priority 2: Database Migrations~~ ✅ COMPLETE
Implemented Flask-Migrate:
- Created `migrations/` directory with Alembic configuration
- Initial migration capturing all tables
- Commands: `flask db migrate`, `flask db upgrade`

### ~~Priority 3: Async Support~~ ✅ COMPLETE
Created `async_scraper.py` with:
- `AsyncParkrunScraper` - async parkrun scraping using aiohttp
- `AsyncPowerOf10Scraper` - async Power of 10 scraping
- `fetch_multiple_athletes()` - concurrent multi-athlete fetching
- `run_async()` helper for sync/async interop

### ~~Priority 4: UX Improvements~~ ✅ COMPLETE
Added to templates:
- Loading spinner with status messages
- Cache age display ("Updated 2h 30m ago")
- Force refresh button to bypass cache

---

## Future Enhancements

### Low Priority Items

| Item | Description |
|------|-------------|
| Redis rate limiting | Persist rate limits across restarts |
| Database connection pooling | Improve concurrent DB performance |
| Multi-worker deployment | Scale to 2-4 workers with async refactoring |
| Export functionality | CSV/JSON export of athlete data |
| Historical trend graphs | Visualization of performance over time |

---

## Deployment Notes

- Currently single-worker; can scale to 2-4 with async refactoring
- Rate limiting won't persist across restarts; consider Redis
- Health check endpoint properly configured for Railway
- Environment variables: DATABASE_URL, SCRAPER_API_KEY, REFRESH_COOLDOWN_HOURS
