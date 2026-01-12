"""
Parkrun "How Fast Am I" - Flask Web Application
Compare your parkrun times to UK and worldwide averages.
Also supports Power of 10 for multi-distance analysis.
"""

import os
from flask import Flask, render_template, request

from scraper import ParkrunScraper
from po10_scraper import PowerOf10Scraper
from comparisons import get_full_comparison, seconds_to_time_str
from distance_comparisons import get_all_distance_comparisons, get_distance_comparison
from age_grading import calculate_age_grade, get_age_grade_category, seconds_to_time_str as ag_time_str

app = Flask(__name__)
parkrun_scraper = ParkrunScraper()
po10_scraper = PowerOf10Scraper()


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page - form and results."""
    results = None
    error = None
    comparison = None

    if request.method == 'POST':
        athlete_id = request.form.get('athlete_id', '').strip()

        if not athlete_id:
            error = "Please enter a parkrun ID"
        elif not athlete_id.isdigit():
            error = "Parkrun ID should be a number (e.g., 123456)"
        else:
            # Fetch athlete data
            results = parkrun_scraper.get_athlete_results(athlete_id)

            if results.get('error'):
                error = results['error']
                results = None
            elif results.get('total_runs', 0) == 0:
                error = f"No parkrun results found for athlete ID {athlete_id}. Please check the ID is correct."
                results = None
            elif results.get('stats') and results['stats'].get('average_seconds'):
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

    return render_template(
        'index.html',
        results=results,
        error=error,
        comparison=comparison
    )


@app.route('/power-of-10', methods=['GET', 'POST'])
def power_of_10():
    """Power of 10 multi-distance analysis page."""
    results = None
    error = None
    distance_comparisons = None

    if request.method == 'POST':
        athlete_id = request.form.get('athlete_id', '').strip()

        if not athlete_id:
            error = "Please enter a Power of 10 athlete ID"
        elif not athlete_id.isdigit():
            error = "Athlete ID should be a number"
        else:
            results = po10_scraper.get_athlete_by_id(athlete_id)

            if results.get('error'):
                error = results['error']
                results = None
            elif not results.get('pbs'):
                error = f"No PBs found for athlete ID {athlete_id}"
                results = None
            else:
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

    return render_template(
        'power_of_10.html',
        results=results,
        error=error,
        distance_comparisons=distance_comparisons
    )


@app.route('/health')
def health():
    """Health check endpoint for Railway."""
    return {'status': 'healthy'}, 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
