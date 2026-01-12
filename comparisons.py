"""
Comparison data and ranking logic for parkrun times.
Data sourced from:
- parkrun.org.uk statistics
- runninglevel.com 5K times
- Running research and surveys
"""

from typing import Optional


def time_str_to_seconds(time_str: str) -> int:
    """Convert MM:SS or HH:MM:SS to seconds."""
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def seconds_to_time_str(seconds: int) -> str:
    """Convert seconds to MM:SS or HH:MM:SS."""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


# Parkrun averages (in seconds)
PARKRUN_AVERAGES = {
    'global': {
        'name': 'Global Parkrun Average',
        'time': time_str_to_seconds('32:00'),
        'description': 'Average across all 2,600+ parkrun events worldwide'
    },
    'uk': {
        'name': 'UK Parkrun Average',
        'time': time_str_to_seconds('29:30'),
        'description': 'Average across UK parkrun events'
    },
    'uk_male': {
        'name': 'UK Male Average',
        'time': time_str_to_seconds('30:29'),
        'description': 'Average for male parkrunners in the UK'
    },
    'uk_female': {
        'name': 'UK Female Average',
        'time': time_str_to_seconds('33:52'),
        'description': 'Average for female parkrunners in the UK'
    },
}

# Country 5K averages (in seconds) - from race results data
COUNTRY_AVERAGES = {
    'uk': {
        'name': 'United Kingdom',
        'overall': time_str_to_seconds('32:11'),
        'male': time_str_to_seconds('30:29'),
        'female': time_str_to_seconds('33:52')
    },
    'usa': {
        'name': 'United States',
        'overall': time_str_to_seconds('32:23'),
        'male': time_str_to_seconds('31:26'),
        'female': time_str_to_seconds('33:21')
    },
    'australia': {
        'name': 'Australia',
        'overall': time_str_to_seconds('32:50'),
        'male': time_str_to_seconds('31:03'),
        'female': time_str_to_seconds('34:38')
    },
    'canada': {
        'name': 'Canada',
        'overall': time_str_to_seconds('33:41'),
        'male': time_str_to_seconds('32:03'),
        'female': time_str_to_seconds('35:19')
    },
    'global': {
        'name': 'Worldwide',
        'overall': time_str_to_seconds('34:29'),
        'male': time_str_to_seconds('33:08'),
        'female': time_str_to_seconds('35:50')
    }
}

# 5K times by ability level (from runninglevel.com)
# Format: age -> {level -> seconds}
MALE_5K_TIMES = {
    20: {
        'beginner': time_str_to_seconds('31:29'),
        'novice': time_str_to_seconds('27:00'),
        'intermediate': time_str_to_seconds('22:31'),
        'advanced': time_str_to_seconds('19:44'),
        'elite': time_str_to_seconds('17:40')
    },
    25: {
        'beginner': time_str_to_seconds('31:29'),
        'novice': time_str_to_seconds('26:45'),
        'intermediate': time_str_to_seconds('22:18'),
        'advanced': time_str_to_seconds('19:32'),
        'elite': time_str_to_seconds('17:29')
    },
    30: {
        'beginner': time_str_to_seconds('31:29'),
        'novice': time_str_to_seconds('26:52'),
        'intermediate': time_str_to_seconds('22:24'),
        'advanced': time_str_to_seconds('19:37'),
        'elite': time_str_to_seconds('17:33')
    },
    35: {
        'beginner': time_str_to_seconds('32:05'),
        'novice': time_str_to_seconds('27:22'),
        'intermediate': time_str_to_seconds('22:49'),
        'advanced': time_str_to_seconds('19:59'),
        'elite': time_str_to_seconds('17:53')
    },
    40: {
        'beginner': time_str_to_seconds('33:09'),
        'novice': time_str_to_seconds('28:17'),
        'intermediate': time_str_to_seconds('23:43'),
        'advanced': time_str_to_seconds('20:46'),
        'elite': time_str_to_seconds('18:36')
    },
    45: {
        'beginner': time_str_to_seconds('34:32'),
        'novice': time_str_to_seconds('29:28'),
        'intermediate': time_str_to_seconds('24:32'),
        'advanced': time_str_to_seconds('21:29'),
        'elite': time_str_to_seconds('19:14')
    },
    50: {
        'beginner': time_str_to_seconds('36:08'),
        'novice': time_str_to_seconds('30:50'),
        'intermediate': time_str_to_seconds('25:41'),
        'advanced': time_str_to_seconds('22:29'),
        'elite': time_str_to_seconds('20:08')
    },
    55: {
        'beginner': time_str_to_seconds('37:58'),
        'novice': time_str_to_seconds('32:22'),
        'intermediate': time_str_to_seconds('26:58'),
        'advanced': time_str_to_seconds('23:36'),
        'elite': time_str_to_seconds('21:08')
    },
    60: {
        'beginner': time_str_to_seconds('38:53'),
        'novice': time_str_to_seconds('33:10'),
        'intermediate': time_str_to_seconds('27:49'),
        'advanced': time_str_to_seconds('24:22'),
        'elite': time_str_to_seconds('21:49')
    },
    65: {
        'beginner': time_str_to_seconds('42:27'),
        'novice': time_str_to_seconds('36:12'),
        'intermediate': time_str_to_seconds('30:09'),
        'advanced': time_str_to_seconds('26:24'),
        'elite': time_str_to_seconds('23:38')
    },
    70: {
        'beginner': time_str_to_seconds('46:37'),
        'novice': time_str_to_seconds('39:46'),
        'intermediate': time_str_to_seconds('33:08'),
        'advanced': time_str_to_seconds('29:01'),
        'elite': time_str_to_seconds('25:58')
    }
}

FEMALE_5K_TIMES = {
    20: {
        'beginner': time_str_to_seconds('35:27'),
        'novice': time_str_to_seconds('30:42'),
        'intermediate': time_str_to_seconds('26:07'),
        'advanced': time_str_to_seconds('23:04'),
        'elite': time_str_to_seconds('20:47')
    },
    25: {
        'beginner': time_str_to_seconds('35:27'),
        'novice': time_str_to_seconds('30:25'),
        'intermediate': time_str_to_seconds('25:52'),
        'advanced': time_str_to_seconds('22:51'),
        'elite': time_str_to_seconds('20:35')
    },
    30: {
        'beginner': time_str_to_seconds('35:27'),
        'novice': time_str_to_seconds('30:33'),
        'intermediate': time_str_to_seconds('25:59'),
        'advanced': time_str_to_seconds('22:57'),
        'elite': time_str_to_seconds('20:41')
    },
    35: {
        'beginner': time_str_to_seconds('35:47'),
        'novice': time_str_to_seconds('30:50'),
        'intermediate': time_str_to_seconds('26:13'),
        'advanced': time_str_to_seconds('23:10'),
        'elite': time_str_to_seconds('20:52')
    },
    40: {
        'beginner': time_str_to_seconds('36:25'),
        'novice': time_str_to_seconds('31:23'),
        'intermediate': time_str_to_seconds('26:49'),
        'advanced': time_str_to_seconds('23:42'),
        'elite': time_str_to_seconds('21:22')
    },
    45: {
        'beginner': time_str_to_seconds('38:09'),
        'novice': time_str_to_seconds('32:53'),
        'intermediate': time_str_to_seconds('27:58'),
        'advanced': time_str_to_seconds('24:42'),
        'elite': time_str_to_seconds('22:16')
    },
    50: {
        'beginner': time_str_to_seconds('40:19'),
        'novice': time_str_to_seconds('34:44'),
        'intermediate': time_str_to_seconds('29:32'),
        'advanced': time_str_to_seconds('26:05'),
        'elite': time_str_to_seconds('23:30')
    },
    55: {
        'beginner': time_str_to_seconds('42:54'),
        'novice': time_str_to_seconds('36:57'),
        'intermediate': time_str_to_seconds('31:25'),
        'advanced': time_str_to_seconds('27:45'),
        'elite': time_str_to_seconds('25:00')
    },
    60: {
        'beginner': time_str_to_seconds('44:29'),
        'novice': time_str_to_seconds('38:18'),
        'intermediate': time_str_to_seconds('32:47'),
        'advanced': time_str_to_seconds('28:58'),
        'elite': time_str_to_seconds('26:06')
    },
    65: {
        'beginner': time_str_to_seconds('49:03'),
        'novice': time_str_to_seconds('42:15'),
        'intermediate': time_str_to_seconds('35:56'),
        'advanced': time_str_to_seconds('31:44'),
        'elite': time_str_to_seconds('28:36')
    },
    70: {
        'beginner': time_str_to_seconds('54:27'),
        'novice': time_str_to_seconds('46:55'),
        'intermediate': time_str_to_seconds('39:54'),
        'advanced': time_str_to_seconds('35:15'),
        'elite': time_str_to_seconds('31:46')
    }
}

# Percentile distribution for parkrun times (estimated from large dataset analysis)
# Maps seconds to approximate percentile (faster than X% of runners)
# Based on UK parkrun distribution
PERCENTILE_THRESHOLDS = [
    (time_str_to_seconds('15:00'), 99.9),  # Sub-15: Top 0.1%
    (time_str_to_seconds('17:00'), 99),    # Sub-17: Top 1%
    (time_str_to_seconds('18:00'), 98),    # Sub-18: Top 2%
    (time_str_to_seconds('19:00'), 95),    # Sub-19: Top 5%
    (time_str_to_seconds('20:00'), 90),    # Sub-20: Top 10%
    (time_str_to_seconds('21:00'), 85),    # Sub-21: Top 15%
    (time_str_to_seconds('22:00'), 80),    # Sub-22: Top 20%
    (time_str_to_seconds('23:00'), 75),    # Sub-23: Top 25%
    (time_str_to_seconds('24:00'), 70),    # Sub-24: Top 30%
    (time_str_to_seconds('25:00'), 65),    # Sub-25: Top 35%
    (time_str_to_seconds('26:00'), 60),    # Sub-26: Top 40%
    (time_str_to_seconds('27:00'), 55),    # Sub-27: Top 45%
    (time_str_to_seconds('28:00'), 52),    # Sub-28: ~Top 48%
    (time_str_to_seconds('29:00'), 50),    # Sub-29: Median
    (time_str_to_seconds('30:00'), 47),    # Sub-30: Top 53%
    (time_str_to_seconds('32:00'), 42),    # Sub-32: ~Global average
    (time_str_to_seconds('35:00'), 35),    # Sub-35
    (time_str_to_seconds('38:00'), 28),    # Sub-38
    (time_str_to_seconds('40:00'), 23),    # Sub-40
    (time_str_to_seconds('45:00'), 15),    # Sub-45
    (time_str_to_seconds('50:00'), 10),    # Sub-50
    (time_str_to_seconds('55:00'), 6),     # Sub-55
    (time_str_to_seconds('60:00'), 3),     # Sub-60
]


def get_percentile(time_seconds: int) -> float:
    """
    Get approximate percentile for a given time.
    Returns the percentage of runners you're faster than.
    """
    for threshold, percentile in PERCENTILE_THRESHOLDS:
        if time_seconds <= threshold:
            return percentile

    # Slower than all thresholds
    return 1.0


def get_ability_level(time_seconds: int, age: int = 30, gender: str = 'male') -> str:
    """
    Determine ability level based on time, age, and gender.
    Returns: 'elite', 'advanced', 'intermediate', 'novice', or 'beginner'
    """
    # Find closest age bracket
    times_table = MALE_5K_TIMES if gender.lower() == 'male' else FEMALE_5K_TIMES
    ages = sorted(times_table.keys())

    closest_age = min(ages, key=lambda x: abs(x - age))
    thresholds = times_table[closest_age]

    if time_seconds <= thresholds['elite']:
        return 'elite'
    elif time_seconds <= thresholds['advanced']:
        return 'advanced'
    elif time_seconds <= thresholds['intermediate']:
        return 'intermediate'
    elif time_seconds <= thresholds['novice']:
        return 'novice'
    else:
        return 'beginner'


def compare_to_averages(time_seconds: int) -> list:
    """
    Compare a time to various averages.
    Returns a list of comparison dicts.
    """
    comparisons = []

    # Compare to parkrun averages
    for key, data in PARKRUN_AVERAGES.items():
        diff = data['time'] - time_seconds
        faster = diff > 0

        comparisons.append({
            'category': 'Parkrun',
            'name': data['name'],
            'benchmark_time': seconds_to_time_str(data['time']),
            'benchmark_seconds': data['time'],
            'difference': abs(diff),
            'difference_str': seconds_to_time_str(abs(diff)),
            'faster': faster,
            'description': data['description']
        })

    return comparisons


def compare_to_countries(time_seconds: int) -> list:
    """Compare a time to country averages."""
    comparisons = []

    for key, data in COUNTRY_AVERAGES.items():
        diff = data['overall'] - time_seconds
        faster = diff > 0

        comparisons.append({
            'country': data['name'],
            'average_time': seconds_to_time_str(data['overall']),
            'average_seconds': data['overall'],
            'difference': abs(diff),
            'difference_str': seconds_to_time_str(abs(diff)),
            'faster': faster
        })

    return comparisons


def get_rating_message(percentile: float, ability: str) -> str:
    """Generate a friendly rating message based on performance."""
    if percentile >= 99:
        return "Incredible! You're among the fastest parkrunners in the world!"
    elif percentile >= 95:
        return "Outstanding! You're an elite-level runner!"
    elif percentile >= 90:
        return "Excellent! You're faster than 90% of parkrunners!"
    elif percentile >= 80:
        return "Great job! You're a strong runner, faster than 80% of participants!"
    elif percentile >= 70:
        return "Well done! You're faster than most parkrunners!"
    elif percentile >= 50:
        return "Good going! You're faster than the average parkrunner!"
    elif percentile >= 30:
        return "Keep it up! Every parkrun makes you stronger!"
    else:
        return "You're doing great! The important thing is you're out there running!"


def get_full_comparison(time_seconds: int, age: Optional[int] = None, gender: Optional[str] = None) -> dict:
    """
    Get a complete comparison analysis for a given time.
    """
    percentile = get_percentile(time_seconds)

    # Use defaults if age/gender not provided
    effective_age = age if age else 35
    effective_gender = gender if gender else 'male'

    ability = get_ability_level(time_seconds, effective_age, effective_gender)

    return {
        'time_seconds': time_seconds,
        'time_str': seconds_to_time_str(time_seconds),
        'percentile': percentile,
        'ability_level': ability,
        'rating_message': get_rating_message(percentile, ability),
        'parkrun_comparisons': compare_to_averages(time_seconds),
        'country_comparisons': compare_to_countries(time_seconds),
    }


# For testing
if __name__ == "__main__":
    # Test with a 25-minute time
    test_time = time_str_to_seconds("25:00")
    result = get_full_comparison(test_time, age=35, gender='male')
    print(f"Time: {result['time_str']}")
    print(f"Percentile: Faster than {result['percentile']}% of runners")
    print(f"Ability Level: {result['ability_level']}")
    print(f"Rating: {result['rating_message']}")
