"""
"How Fast Am I?" - Flask Web Application
Compare your running times to worldwide averages.

Supports:
- Parkrun (UK/Global) - 5K parkrun results
- Power of 10 (UK) - Multi-distance track & road results
- Athlinks (USA) - Multi-distance road race results
"""

import logging
import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from flask_migrate import Migrate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Minimum hours before refresh is allowed (prevents abuse)
REFRESH_COOLDOWN_HOURS = int(os.environ.get('REFRESH_COOLDOWN_HOURS', 6))

from scraper import ParkrunScraper
from po10_scraper import PowerOf10Scraper
# from athlinks_scraper import AthlinksScraper  # Disabled until API key received
from utils import seconds_to_time_str, validate_parkrun_id, validate_po10_id
from comparisons import get_full_comparison, get_percentile, DISTANCE_AVERAGES
from distance_comparisons import get_all_distance_comparisons, get_distance_comparison
from age_grading import calculate_age_grade, get_age_grade_category
from models import db, ParkrunAthlete, PowerOf10Athlete, AthlinksAthlete, Lookup

app = Flask(__name__)

# Secret key for session management (set via env var in production)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(32).hex())

# Database configuration
database_url = os.environ.get('DATABASE_URL', '')
# Railway uses postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///athletes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize Flask-Migrate for database migrations
migrate = Migrate(app, db)

# Rate limiting configuration to protect ScraperAPI credits
# Uses in-memory storage (resets on app restart)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Create tables on startup (for development/new deployments)
# For production, use: flask db upgrade
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created/verified successfully")
    except OperationalError as e:
        logger.error(f"Database connection error: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")

    # Legacy migration support: Add recent_results_json column if it doesn't exist
    # New migrations should use: flask db migrate -m "description"
    try:
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        if inspector.has_table('parkrun_athletes'):
            columns = [col['name'] for col in inspector.get_columns('parkrun_athletes')]
            if 'recent_results_json' not in columns:
                db.session.execute(text('ALTER TABLE parkrun_athletes ADD COLUMN recent_results_json TEXT'))
                db.session.commit()
                logger.info("Migration: Added recent_results_json column")
    except OperationalError as e:
        db.session.rollback()
        logger.debug(f"Migration check (table may not exist yet): {e}")
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.debug(f"Migration check: {e}")

parkrun_scraper = ParkrunScraper()
po10_scraper = PowerOf10Scraper()
# athlinks_scraper = AthlinksScraper()  # Disabled until API key received


def save_parkrun_athlete(athlete_id: str, results: dict):
    """Save or update parkrun athlete data in the database."""
    try:
        stats = results.get('stats', {})

        # Store last 10 results as JSON for display
        recent_results = results.get('results', [])[:10]
        recent_results_json = json.dumps(recent_results) if recent_results else None

        athlete = ParkrunAthlete.query.filter_by(athlete_id=athlete_id).first()

        if athlete:
            # Update existing record
            athlete.name = results.get('name')
            athlete.total_runs = results.get('total_runs')
            athlete.best_time_seconds = stats.get('best_seconds')
            athlete.average_time_seconds = stats.get('average_seconds')
            athlete.typical_avg_seconds = stats.get('typical_avg_seconds')
            athlete.recent_avg_seconds = stats.get('recent_avg_seconds')
            athlete.best_time = stats.get('best_time')
            athlete.average_time = stats.get('average_time')
            athlete.typical_avg_time = stats.get('typical_avg_time')
            athlete.recent_avg_time = stats.get('recent_avg_time')
            athlete.avg_age_grade = stats.get('avg_age_grade')
            athlete.recent_avg_age_grade = stats.get('recent_avg_age_grade')
            athlete.pb_date = stats.get('pb_date')
            athlete.pb_event = stats.get('pb_event')
            athlete.pb_age = stats.get('pb_age')
            athlete.trend = stats.get('trend')
            athlete.trend_message = stats.get('trend_message')
            athlete.outlier_count = stats.get('outlier_count', 0)
            athlete.normal_run_count = stats.get('normal_run_count', 0)
            athlete.recent_results_json = recent_results_json
            athlete.updated_at = datetime.utcnow()
            athlete.lookup_count += 1
            athlete.last_lookup_at = datetime.utcnow()
        else:
            # Create new record
            athlete = ParkrunAthlete(
                athlete_id=athlete_id,
                name=results.get('name'),
                total_runs=results.get('total_runs'),
                best_time_seconds=stats.get('best_seconds'),
                average_time_seconds=stats.get('average_seconds'),
                typical_avg_seconds=stats.get('typical_avg_seconds'),
                recent_avg_seconds=stats.get('recent_avg_seconds'),
                best_time=stats.get('best_time'),
                average_time=stats.get('average_time'),
                typical_avg_time=stats.get('typical_avg_time'),
                recent_avg_time=stats.get('recent_avg_time'),
                avg_age_grade=stats.get('avg_age_grade'),
                recent_avg_age_grade=stats.get('recent_avg_age_grade'),
                pb_date=stats.get('pb_date'),
                pb_event=stats.get('pb_event'),
                pb_age=stats.get('pb_age'),
                trend=stats.get('trend'),
                trend_message=stats.get('trend_message'),
                outlier_count=stats.get('outlier_count', 0),
                normal_run_count=stats.get('normal_run_count', 0),
                recent_results_json=recent_results_json,
            )
            db.session.add(athlete)

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error saving parkrun athlete: {e}")


def save_po10_athlete(athlete_id: str, results: dict, overall_stats: dict = None):
    """Save or update Power of 10 athlete data in the database."""
    try:
        athlete = PowerOf10Athlete.query.filter_by(athlete_id=athlete_id).first()

        pbs_json = json.dumps(results.get('pbs', {}))

        if athlete:
            # Update existing record
            athlete.name = results.get('name')
            athlete.club = results.get('club')
            athlete.gender = results.get('gender')
            athlete.age_group = results.get('age_group')
            athlete.pbs_json = pbs_json
            if overall_stats:
                athlete.overall_percentile = overall_stats.get('percentile')
                athlete.overall_age_grade = overall_stats.get('age_grade')
                athlete.overall_ability_level = overall_stats.get('ability_level')
            athlete.updated_at = datetime.utcnow()
            athlete.lookup_count += 1
            athlete.last_lookup_at = datetime.utcnow()
        else:
            # Create new record
            athlete = PowerOf10Athlete(
                athlete_id=athlete_id,
                name=results.get('name'),
                club=results.get('club'),
                gender=results.get('gender'),
                age_group=results.get('age_group'),
                pbs_json=pbs_json,
                overall_percentile=overall_stats.get('percentile') if overall_stats else None,
                overall_age_grade=overall_stats.get('age_grade') if overall_stats else None,
                overall_ability_level=overall_stats.get('ability_level') if overall_stats else None,
            )
            db.session.add(athlete)

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error saving PO10 athlete: {e}")


def save_athlinks_athlete(athlete_id: str, results: dict, overall_stats: dict = None):
    """Save or update Athlinks athlete data in the database."""
    try:
        athlete = AthlinksAthlete.query.filter_by(athlete_id=athlete_id).first()

        pbs_json = json.dumps(results.get('pbs', {}))
        results_json = json.dumps(results.get('results', [])[:20])  # Store last 20 races
        stats = results.get('stats', {})

        if athlete:
            # Update existing record
            athlete.name = results.get('name')
            athlete.total_races = results.get('total_races', 0)
            athlete.total_distance_km = stats.get('total_distance_km')
            athlete.total_distance_miles = stats.get('total_distance_miles')
            athlete.pbs_json = pbs_json
            athlete.results_json = results_json
            if overall_stats:
                athlete.overall_percentile = overall_stats.get('percentile')
                athlete.overall_ability_level = overall_stats.get('ability_level')
            athlete.updated_at = datetime.utcnow()
            athlete.lookup_count += 1
            athlete.last_lookup_at = datetime.utcnow()
        else:
            # Create new record
            athlete = AthlinksAthlete(
                athlete_id=athlete_id,
                name=results.get('name'),
                total_races=results.get('total_races', 0),
                total_distance_km=stats.get('total_distance_km'),
                total_distance_miles=stats.get('total_distance_miles'),
                pbs_json=pbs_json,
                results_json=results_json,
                overall_percentile=overall_stats.get('percentile') if overall_stats else None,
                overall_ability_level=overall_stats.get('ability_level') if overall_stats else None,
            )
            db.session.add(athlete)

        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Error saving Athlinks athlete: {e}")


def get_cached_athlinks_athlete(athlete_id: str, fresh_only: bool = True) -> dict:
    """
    Try to get Athlinks athlete from database cache.

    Args:
        athlete_id: The Athlinks athlete ID
        fresh_only: If True, only return if cache is fresh (< REFRESH_COOLDOWN_HOURS old)
    """
    try:
        athlete = AthlinksAthlete.query.filter_by(athlete_id=athlete_id).first()
        if athlete:
            # Check if cache is fresh enough
            if fresh_only and not is_cache_fresh(athlete.updated_at):
                return None  # Cache is stale, need to refresh

            # Parse data from JSON
            pbs = json.loads(athlete.pbs_json) if athlete.pbs_json else {}
            results = json.loads(athlete.results_json) if athlete.results_json else []

            return {
                'name': athlete.name,
                'athlete_id': athlete.athlete_id,
                'total_races': athlete.total_races,
                'pbs': pbs,
                'results': results,
                'stats': {
                    'total_distance_km': athlete.total_distance_km,
                    'total_distance_miles': athlete.total_distance_miles,
                },
                'overall': {
                    'percentile': athlete.overall_percentile,
                    'ability_level': athlete.overall_ability_level,
                } if athlete.overall_percentile else None,
                'from_cache': True,
                'cached_at': athlete.updated_at.isoformat() if athlete.updated_at else None,
            }
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing cached Athlinks athlete JSON: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Database error getting cached Athlinks athlete: {e}")
    return None


def log_lookup(source: str, athlete_id: str, athlete_name: str = None):
    """Log a lookup to the database for analytics (called on every successful lookup)."""
    try:
        lookup = Lookup(
            source=source,
            athlete_id=athlete_id,
            athlete_name=athlete_name,
            ip_address=request.remote_addr
        )
        db.session.add(lookup)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.warning(f"Error logging lookup: {e}")


def is_cache_fresh(updated_at: datetime) -> bool:
    """Check if cached data is fresh enough (less than REFRESH_COOLDOWN_HOURS old)."""
    if not updated_at:
        return False
    cache_age = datetime.utcnow() - updated_at
    return cache_age < timedelta(hours=REFRESH_COOLDOWN_HOURS)


def get_cached_parkrun_athlete(athlete_id: str, fresh_only: bool = True) -> dict:
    """
    Try to get parkrun athlete from database cache.

    Args:
        athlete_id: The parkrun athlete ID
        fresh_only: If True, only return if cache is fresh (< REFRESH_COOLDOWN_HOURS old)
    """
    try:
        athlete = ParkrunAthlete.query.filter_by(athlete_id=athlete_id).first()
        if athlete:
            # Check if cache is fresh enough
            if fresh_only and not is_cache_fresh(athlete.updated_at):
                return None  # Cache is stale, need to refresh

            # Parse recent results from JSON
            recent_results = []
            if athlete.recent_results_json:
                try:
                    recent_results = json.loads(athlete.recent_results_json)
                except json.JSONDecodeError:
                    recent_results = []

            return {
                'name': athlete.name,
                'athlete_id': athlete.athlete_id,
                'total_runs': athlete.total_runs,
                'results': recent_results,
                'stats': {
                    'best_seconds': athlete.best_time_seconds,
                    'average_seconds': athlete.average_time_seconds,
                    'typical_avg_seconds': athlete.typical_avg_seconds,
                    'recent_avg_seconds': athlete.recent_avg_seconds,
                    'best_time': athlete.best_time,
                    'average_time': athlete.average_time,
                    'typical_avg_time': athlete.typical_avg_time,
                    'recent_avg_time': athlete.recent_avg_time,
                    'avg_age_grade': athlete.avg_age_grade,
                    'recent_avg_age_grade': athlete.recent_avg_age_grade,
                    'pb_date': athlete.pb_date,
                    'pb_event': athlete.pb_event,
                    'pb_age': athlete.pb_age,
                    'trend': athlete.trend,
                    'trend_message': athlete.trend_message,
                    'outlier_count': athlete.outlier_count or 0,
                    'normal_run_count': athlete.normal_run_count or 0,
                    'total_runs': athlete.total_runs,
                    'typical_median_seconds': athlete.typical_avg_seconds,  # Approximate
                },
                'from_cache': True,
                'cached_at': athlete.updated_at.isoformat() if athlete.updated_at else None,
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error getting cached parkrun athlete: {e}")
    return None


def get_cached_po10_athlete(athlete_id: str, fresh_only: bool = True) -> dict:
    """
    Try to get Power of 10 athlete from database cache.

    Args:
        athlete_id: The Power of 10 athlete ID
        fresh_only: If True, only return if cache is fresh (< REFRESH_COOLDOWN_HOURS old)
    """
    try:
        athlete = PowerOf10Athlete.query.filter_by(athlete_id=athlete_id).first()
        if athlete:
            # Check if cache is fresh enough
            if fresh_only and not is_cache_fresh(athlete.updated_at):
                return None  # Cache is stale, need to refresh

            # Parse PBs from JSON
            pbs = json.loads(athlete.pbs_json) if athlete.pbs_json else {}

            return {
                'name': athlete.name,
                'athlete_id': athlete.athlete_id,
                'club': athlete.club,
                'gender': athlete.gender,
                'age_group': athlete.age_group,
                'pbs': pbs,
                'overall': {
                    'percentile': athlete.overall_percentile,
                    'age_grade': athlete.overall_age_grade,
                    'ability_level': athlete.overall_ability_level,
                } if athlete.overall_percentile else None,
                'from_cache': True,
                'cached_at': athlete.updated_at.isoformat() if athlete.updated_at else None,
            }
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing cached PO10 athlete JSON: {e}")
    except SQLAlchemyError as e:
        logger.error(f"Database error getting cached PO10 athlete: {e}")
    return None


@app.route('/', methods=['GET', 'POST'])
@limiter.limit("10 per minute", methods=["POST"])  # Stricter limit for parkrun (uses ScraperAPI)
@limiter.limit("30 per hour", methods=["POST"])
def index():
    """Main page - form and results."""
    results = None
    error = None
    comparison = None
    from_cache = False
    cache_age_str = None
    force_refresh = request.form.get('force_refresh') == '1'

    if request.method == 'POST':
        athlete_id_input = request.form.get('athlete_id', '')

        # Validate the athlete ID
        validation = validate_parkrun_id(athlete_id_input)
        if not validation:
            error = validation.error_message
        else:
            athlete_id = validation.sanitized_id
            # Check for fresh cached data (less than REFRESH_COOLDOWN_HOURS old)
            # Skip cache if force_refresh is requested
            cached = None if force_refresh else get_cached_parkrun_athlete(athlete_id, fresh_only=True)
            if cached:
                results = cached
                from_cache = True
                # Calculate cache age for display
                if cached.get('cached_at'):
                    try:
                        cached_time = datetime.fromisoformat(cached['cached_at'])
                        age = datetime.utcnow() - cached_time
                        hours = int(age.total_seconds() // 3600)
                        minutes = int((age.total_seconds() % 3600) // 60)
                        if hours > 0:
                            cache_age_str = f"{hours}h {minutes}m ago"
                        else:
                            cache_age_str = f"{minutes}m ago"
                    except (ValueError, TypeError):
                        cache_age_str = "recently"
            else:
                # No fresh cache - scrape new data
                results = parkrun_scraper.get_athlete_results(athlete_id)

                if results.get('error'):
                    # Scraping failed - try stale cache as fallback
                    stale_cache = get_cached_parkrun_athlete(athlete_id, fresh_only=False)
                    if stale_cache:
                        results = stale_cache
                        from_cache = True
                    else:
                        error = results['error']
                        results = None
                elif results.get('total_runs', 0) == 0:
                    error = f"No parkrun results found for athlete ID {athlete_id}. Please check the ID is correct."
                    results = None
                else:
                    # Save/update athlete in database
                    save_parkrun_athlete(athlete_id, results)

            # Generate comparisons if we have valid results
            if results and results.get('stats') and results['stats'].get('average_seconds'):
                stats = results['stats']

                # Get comparison data based on TYPICAL time (excluding outliers)
                typical_time = stats.get('typical_avg_seconds', stats['average_seconds'])
                comparison = get_full_comparison(typical_time)

                # Comparison for best time (PB)
                if stats.get('best_seconds'):
                    comparison['best_comparison'] = get_full_comparison(
                        stats['best_seconds']
                    )

                # Comparison for current form (recent runs)
                if stats.get('recent_avg_seconds'):
                    comparison['current_form_comparison'] = get_full_comparison(
                        stats['recent_avg_seconds']
                    )

                # Comparison for all-time average (including outliers)
                comparison['alltime_comparison'] = get_full_comparison(
                    stats['average_seconds']
                )

                # Log every successful lookup
                log_lookup('parkrun', athlete_id, results.get('name'))

    return render_template(
        'index.html',
        results=results,
        error=error,
        comparison=comparison,
        from_cache=from_cache,
        cache_age_str=cache_age_str,
        refresh_cooldown_hours=REFRESH_COOLDOWN_HOURS
    )


@app.route('/power-of-10', methods=['GET', 'POST'])
@limiter.limit("15 per minute", methods=["POST"])  # Power of 10 (no ScraperAPI, more lenient)
@limiter.limit("60 per hour", methods=["POST"])
def power_of_10():
    """Power of 10 multi-distance analysis page."""
    results = None
    error = None
    distance_comparisons = None
    from_cache = False
    cache_age_str = None
    force_refresh = request.form.get('force_refresh') == '1'

    if request.method == 'POST':
        athlete_id_input = request.form.get('athlete_id', '')

        # Validate the athlete ID
        validation = validate_po10_id(athlete_id_input)
        if not validation:
            error = validation.error_message
        else:
            athlete_id = validation.sanitized_id
            # Check for fresh cached data (less than REFRESH_COOLDOWN_HOURS old)
            # Skip cache if force_refresh is requested
            cached = None if force_refresh else get_cached_po10_athlete(athlete_id, fresh_only=True)
            if cached and cached.get('pbs'):
                results = cached
                from_cache = True
                # Calculate cache age for display
                if cached.get('cached_at'):
                    try:
                        cached_time = datetime.fromisoformat(cached['cached_at'])
                        age = datetime.utcnow() - cached_time
                        hours = int(age.total_seconds() // 3600)
                        minutes = int((age.total_seconds() % 3600) // 60)
                        if hours > 0:
                            cache_age_str = f"{hours}h {minutes}m ago"
                        else:
                            cache_age_str = f"{minutes}m ago"
                    except (ValueError, TypeError):
                        cache_age_str = "recently"
            else:
                # No fresh cache - scrape new data
                results = po10_scraper.get_athlete_by_id(athlete_id)

                if results.get('error'):
                    # Scraping failed - try stale cache as fallback
                    stale_cache = get_cached_po10_athlete(athlete_id, fresh_only=False)
                    if stale_cache and stale_cache.get('pbs'):
                        results = stale_cache
                        from_cache = True
                    else:
                        error = results['error']
                        results = None
                elif not results.get('pbs'):
                    error = f"No PBs found for athlete ID {athlete_id}"
                    results = None

            # Generate comparisons if we have valid results with PBs
            if results and results.get('pbs'):
                # Get age for comparison (try to parse from age_group like V55)
                age = 35  # Default
                age_group = results.get('age_group', '')
                if age_group:
                    if age_group.startswith('V'):
                        try:
                            age = int(age_group[1:])
                        except ValueError:
                            pass
                    elif age_group == 'SEN':
                        age = 25

                gender = results.get('gender', 'male')

                # Get comparisons for all distances
                distance_comparisons = get_all_distance_comparisons(
                    results['pbs'],
                    age=age,
                    gender=gender
                )

                # Add age grading to each distance
                for distance, data in distance_comparisons.items():
                    ag_pct, ag_time = calculate_age_grade(
                        data['time_seconds'],
                        distance,
                        age,
                        gender
                    )
                    ag_cat, ag_cat_name = get_age_grade_category(ag_pct)
                    data['age_grade'] = ag_pct
                    data['age_graded_time'] = seconds_to_time_str(ag_time) if ag_time else None
                    data['age_grade_category'] = ag_cat
                    data['age_grade_category_name'] = ag_cat_name

                # Calculate overall stats
                if distance_comparisons:
                    percentiles = [d['percentile'] for d in distance_comparisons.values()]
                    avg_percentile = sum(percentiles) / len(percentiles)

                    # Calculate average age grade
                    age_grades = [d['age_grade'] for d in distance_comparisons.values() if d.get('age_grade')]
                    avg_age_grade = sum(age_grades) / len(age_grades) if age_grades else 0

                    # Determine overall ability level (use most common or highest)
                    levels = [d['ability_level'] for d in distance_comparisons.values()]
                    level_priority = {'elite': 5, 'advanced': 4, 'intermediate': 3, 'novice': 2, 'beginner': 1}
                    # Use the median level
                    sorted_levels = sorted(levels, key=lambda x: level_priority.get(x, 0))
                    overall_level = sorted_levels[len(sorted_levels) // 2]

                    # Get age grade category for overall
                    overall_ag_cat, overall_ag_cat_name = get_age_grade_category(avg_age_grade)

                    # Generate overall rating message
                    if avg_percentile >= 95:
                        overall_message = "Outstanding multi-distance performance!"
                    elif avg_percentile >= 85:
                        overall_message = "Excellent across all distances!"
                    elif avg_percentile >= 75:
                        overall_message = "Strong performances across the board!"
                    elif avg_percentile >= 60:
                        overall_message = "Solid running at multiple distances!"
                    elif avg_percentile >= 40:
                        overall_message = "Good foundation across distances!"
                    else:
                        overall_message = "Keep training - you're making progress!"

                    results['overall'] = {
                        'percentile': round(avg_percentile, 1),
                        'ability_level': overall_level,
                        'rating_message': overall_message,
                        'distance_count': len(distance_comparisons),
                        'age_grade': round(avg_age_grade, 1),
                        'age_grade_category': overall_ag_cat,
                        'age_grade_category_name': overall_ag_cat_name,
                    }

                    # Save to database (only if freshly scraped)
                    if not from_cache:
                        save_po10_athlete(athlete_id, results, results['overall'])

                    # Log every successful lookup
                    log_lookup('po10', athlete_id, results.get('name'))

    return render_template(
        'power_of_10.html',
        results=results,
        error=error,
        distance_comparisons=distance_comparisons,
        from_cache=from_cache,
        cache_age_str=cache_age_str,
        refresh_cooldown_hours=REFRESH_COOLDOWN_HOURS
    )


@app.route('/athlinks', methods=['GET', 'POST'])
def athlinks_page():
    """Athlinks multi-distance analysis page (USA) - Coming soon with API."""
    # Simplified route - waiting for Athlinks API key
    return render_template(
        'athlinks.html',
        results=None,
        error="Athlinks integration coming soon! Waiting for API approval.",
        distance_comparisons=None
    )


@app.route('/health')
@limiter.exempt
def health():
    """Health check endpoint for Railway."""
    return {'status': 'healthy'}, 200


@app.route('/test')
@limiter.exempt
def test():
    """Simple test endpoint."""
    return 'App is running!', 200


@app.route('/stats')
@limiter.exempt
def stats():
    """Show database statistics."""
    try:
        parkrun_count = ParkrunAthlete.query.count()
        po10_count = PowerOf10Athlete.query.count()
        athlinks_count = AthlinksAthlete.query.count()
        lookup_count = Lookup.query.count()

        # Recent lookups
        recent_lookups = Lookup.query.order_by(Lookup.lookup_at.desc()).limit(10).all()

        return {
            'parkrun_athletes': parkrun_count,
            'po10_athletes': po10_count,
            'athlinks_athletes': athlinks_count,
            'total_lookups': lookup_count,
            'refresh_cooldown_hours': REFRESH_COOLDOWN_HOURS,
            'recent_lookups': [
                {
                    'source': l.source,
                    'athlete_id': l.athlete_id,
                    'name': l.athlete_name,
                    'time': l.lookup_at.isoformat() if l.lookup_at else None
                }
                for l in recent_lookups
            ]
        }
    except SQLAlchemyError as e:
        logger.error(f"Database error in stats endpoint: {e}")
        return {'error': 'Database error retrieving statistics'}, 500


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors."""
    return render_template(
        'error.html',
        error_title="Rate Limit Exceeded",
        error_message="You've made too many requests. Please wait a few minutes before trying again.",
        error_detail=str(e.description)
    ), 429


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
