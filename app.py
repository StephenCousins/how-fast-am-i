"""
Parkrun "How Fast Am I" - Flask Web Application
Compare your parkrun times to UK and worldwide averages.
Also supports Power of 10 for multi-distance analysis.
"""

import os
import json
from datetime import datetime, timedelta
from flask import Flask, render_template, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Minimum hours before refresh is allowed (prevents abuse)
REFRESH_COOLDOWN_HOURS = int(os.environ.get('REFRESH_COOLDOWN_HOURS', 6))

from scraper import ParkrunScraper
from po10_scraper import PowerOf10Scraper
from comparisons import get_full_comparison, seconds_to_time_str
from distance_comparisons import get_all_distance_comparisons, get_distance_comparison
from age_grading import calculate_age_grade, get_age_grade_category, seconds_to_time_str as ag_time_str
from models import db, ParkrunAthlete, PowerOf10Athlete, Lookup

app = Flask(__name__)

# Database configuration
database_url = os.environ.get('DATABASE_URL', '')
# Railway uses postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///athletes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Rate limiting configuration to protect ScraperAPI credits
# Uses in-memory storage (resets on app restart)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

# Create tables on startup
with app.app_context():
    db.create_all()

parkrun_scraper = ParkrunScraper()
po10_scraper = PowerOf10Scraper()


def save_parkrun_athlete(athlete_id: str, results: dict):
    """Save or update parkrun athlete data in the database."""
    try:
        stats = results.get('stats', {})

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
            )
            db.session.add(athlete)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error saving parkrun athlete: {e}")


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
    except Exception as e:
        db.session.rollback()
        print(f"Error saving PO10 athlete: {e}")


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
    except Exception as e:
        db.session.rollback()
        print(f"Error logging lookup: {e}")


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

            return {
                'name': athlete.name,
                'athlete_id': athlete.athlete_id,
                'total_runs': athlete.total_runs,
                'results': [],  # We don't cache individual results
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
    except Exception as e:
        print(f"Error getting cached athlete: {e}")
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
    except Exception as e:
        print(f"Error getting cached PO10 athlete: {e}")
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

    if request.method == 'POST':
        athlete_id = request.form.get('athlete_id', '').strip()

        if not athlete_id:
            error = "Please enter a parkrun ID"
        elif not athlete_id.isdigit():
            error = "Parkrun ID should be a number (e.g., 123456)"
        else:
            # Check for fresh cached data (less than REFRESH_COOLDOWN_HOURS old)
            cached = get_cached_parkrun_athlete(athlete_id, fresh_only=True)
            if cached:
                results = cached
                from_cache = True
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
        comparison=comparison
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

    if request.method == 'POST':
        athlete_id = request.form.get('athlete_id', '').strip()

        if not athlete_id:
            error = "Please enter a Power of 10 athlete ID"
        elif not athlete_id.isdigit():
            error = "Athlete ID should be a number"
        else:
            # Check for fresh cached data (less than REFRESH_COOLDOWN_HOURS old)
            cached = get_cached_po10_athlete(athlete_id, fresh_only=True)
            if cached and cached.get('pbs'):
                results = cached
                from_cache = True
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
                    data['age_graded_time'] = ag_time_str(ag_time) if ag_time else None
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
        distance_comparisons=distance_comparisons
    )


@app.route('/health')
@limiter.exempt
def health():
    """Health check endpoint for Railway."""
    return {'status': 'healthy'}, 200


@app.route('/stats')
@limiter.exempt
def stats():
    """Show database statistics."""
    try:
        parkrun_count = ParkrunAthlete.query.count()
        po10_count = PowerOf10Athlete.query.count()
        lookup_count = Lookup.query.count()

        # Recent lookups
        recent_lookups = Lookup.query.order_by(Lookup.lookup_at.desc()).limit(10).all()

        return {
            'parkrun_athletes': parkrun_count,
            'po10_athletes': po10_count,
            'total_lookups': lookup_count,
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
    except Exception as e:
        return {'error': str(e)}, 500


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
