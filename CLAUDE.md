# How Fast Am I?

Flask web app that compares running times to worldwide averages. Scrapes data from parkrun and Power of 10, then shows percentile rankings and age-graded performance. Flask 3 + Gunicorn, PostgreSQL via SQLAlchemy + Flask-Migrate, Sentry, hosted on Railway.

## Commands

```bash
flask run                          # run locally
pytest                             # tests
flask db upgrade                   # apply migrations
flask db migrate -m "description"  # new migration
```

## Environment variables

- `DATABASE_URL`: PostgreSQL connection string
- `SENTRY_DSN`: Sentry error tracking
- `ENVIRONMENT`: `production` or `development`
- `REFRESH_COOLDOWN_HOURS`: min hours between data refreshes (default 6)

## Key behaviour

- Rate limited via Flask-Limiter.
- Athlete data is cached in PostgreSQL with a refresh cooldown to prevent scraping abuse.
- The Athlinks scraper (`athlinks_scraper.py`) is disabled in `app.py`, awaiting an API key.
- Age grading uses the WMA factors in the `WMA_FACTORS` dict in `age_grading.py` (10M interpolated from 10K and half marathon).

## Where to find more

- `README.md`: setup and Railway deployment.
- `CODE_ANALYSIS.md`: past code review and its fixes; read before a cleanup pass.
