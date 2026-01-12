"""
Comparison data and ranking logic for running times.

Data sources:
- Parkrun averages: parkrun.org.uk statistics (for parkrun-specific comparisons)
- Distance averages & percentiles: RunRepeat.com analysis of 107.9 million race results
  from 70,000+ events (1986-2018) - the largest recreational running dataset available
  https://runrepeat.com/how-do-you-masure-up-the-runners-percentile-calculator
- Age grading: WMA 2023 age grading factors
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

# Global race averages by distance (from RunRepeat 107.9M race results)
# Source: https://runrepeat.com/how-do-you-masure-up-the-runners-percentile-calculator
DISTANCE_AVERAGES = {
    '5k': {
        'name': '5K',
        'distance_km': 5,
        'male': time_str_to_seconds('31:28'),
        'female': time_str_to_seconds('37:28'),
        'overall': time_str_to_seconds('34:00'),  # Approximate weighted average
    },
    '10k': {
        'name': '10K',
        'distance_km': 10,
        'male': time_str_to_seconds('57:15'),
        'female': time_str_to_seconds('1:06:54'),
        'overall': time_str_to_seconds('1:02:08'),
    },
    'half': {
        'name': 'Half Marathon',
        'distance_km': 21.1,
        'male': time_str_to_seconds('1:59:26'),
        'female': time_str_to_seconds('2:14:40'),
        'overall': time_str_to_seconds('2:05:00'),  # Approximate weighted average
    },
    'marathon': {
        'name': 'Marathon',
        'distance_km': 42.2,
        'male': time_str_to_seconds('4:21:03'),
        'female': time_str_to_seconds('4:48:45'),
        'overall': time_str_to_seconds('4:32:49'),
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

# Percentile thresholds by distance (from RunRepeat 107.9M race results)
# Maps seconds to approximate percentile (faster than X% of runners)
# Source: https://runrepeat.com/how-do-you-masure-up-the-runners-percentile-calculator

PERCENTILE_THRESHOLDS_5K = [
    (time_str_to_seconds('15:00'), 99.9),  # Sub-15: Top 0.1%
    (time_str_to_seconds('17:30'), 99),    # Sub-17:30: Top 1% (RunRepeat verified)
    (time_str_to_seconds('19:00'), 97),    # Sub-19: Top 3%
    (time_str_to_seconds('20:00'), 95),    # Sub-20: Top 5%
    (time_str_to_seconds('21:00'), 93),    # Sub-21: Top 7%
    (time_str_to_seconds('22:00'), 91),    # Sub-22: Top 9%
    (time_str_to_seconds('23:00'), 90),    # Sub-23: Top 10% for men (RunRepeat verified)
    (time_str_to_seconds('25:00'), 90),    # Sub-25: Top 10% overall (RunRepeat verified)
    (time_str_to_seconds('27:00'), 80),    # Sub-27: Top 20%
    (time_str_to_seconds('28:00'), 75),    # Sub-28: Top 25%
    (time_str_to_seconds('30:00'), 70),    # Sub-30: Top 30% (RunRepeat verified)
    (time_str_to_seconds('32:00'), 60),    # Sub-32: Top 40%
    (time_str_to_seconds('34:00'), 50),    # Sub-34: Median (near global average)
    (time_str_to_seconds('37:00'), 40),    # Sub-37: Top 60%
    (time_str_to_seconds('40:00'), 30),    # Sub-40: Top 70%
    (time_str_to_seconds('45:00'), 20),    # Sub-45: Top 80%
    (time_str_to_seconds('50:00'), 12),    # Sub-50: Top 88%
    (time_str_to_seconds('55:00'), 7),     # Sub-55: Top 93%
    (time_str_to_seconds('60:00'), 4),     # Sub-60: Top 96%
]

PERCENTILE_THRESHOLDS_10K = [
    (time_str_to_seconds('32:00'), 99.9),  # Sub-32: Top 0.1%
    (time_str_to_seconds('35:00'), 99),    # Sub-35: Top 1%
    (time_str_to_seconds('40:00'), 97),    # Sub-40: Top 3%
    (time_str_to_seconds('45:00'), 93),    # Sub-45: Top 7%
    (time_str_to_seconds('48:11'), 90),    # Sub-48:11: Top 10% (RunRepeat verified)
    (time_str_to_seconds('52:00'), 80),    # Sub-52: Top 20%
    (time_str_to_seconds('55:00'), 70),    # Sub-55: Top 30%
    (time_str_to_seconds('58:00'), 65),    # Sub-58: Top 35%
    (time_str_to_seconds('1:00:00'), 60),  # Sub-60: Top 40% (RunRepeat verified)
    (time_str_to_seconds('1:02:08'), 50),  # Global average = median
    (time_str_to_seconds('1:10:00'), 35),  # Sub-70min: Top 65%
    (time_str_to_seconds('1:20:00'), 20),  # Sub-80min: Top 80%
    (time_str_to_seconds('1:30:00'), 10),  # Sub-90min: Top 90%
]

PERCENTILE_THRESHOLDS_HALF = [
    (time_str_to_seconds('1:10:00'), 99.9),  # Sub-1:10: Top 0.1%
    (time_str_to_seconds('1:23:59'), 99),    # Sub-1:24: Top 1% (RunRepeat verified)
    (time_str_to_seconds('1:30:00'), 97),    # Sub-1:30: Top 3%
    (time_str_to_seconds('1:40:00'), 93),    # Sub-1:40: Top 7%
    (time_str_to_seconds('1:47:10'), 90),    # Sub-1:47:10: Top 10% (RunRepeat verified)
    (time_str_to_seconds('1:50:00'), 85),    # Sub-1:50: Top 15%
    (time_str_to_seconds('1:55:00'), 70),    # Sub-1:55: Top 30%
    (time_str_to_seconds('2:00:00'), 55),    # Sub-2:00: Top 45% (RunRepeat: only 45% sub-2)
    (time_str_to_seconds('2:05:00'), 50),    # ~Global average = median
    (time_str_to_seconds('2:15:00'), 40),    # Sub-2:15: Top 60%
    (time_str_to_seconds('2:30:00'), 25),    # Sub-2:30: Top 75%
    (time_str_to_seconds('2:45:00'), 15),    # Sub-2:45: Top 85%
    (time_str_to_seconds('3:00:00'), 8),     # Sub-3:00: Top 92%
]

PERCENTILE_THRESHOLDS_MARATHON = [
    (time_str_to_seconds('2:30:00'), 99.9),  # Sub-2:30: Top 0.1%
    (time_str_to_seconds('2:50:48'), 99),    # Sub-2:51: Top 1% (RunRepeat verified)
    (time_str_to_seconds('3:00:00'), 97),    # Sub-3:00: Top 3%
    (time_str_to_seconds('3:15:00'), 93),    # Sub-3:15: Top 7%
    (time_str_to_seconds('3:31:46'), 90),    # Sub-3:32: Top 10% (RunRepeat verified)
    (time_str_to_seconds('3:45:00'), 80),    # Sub-3:45: Top 20%
    (time_str_to_seconds('4:00:00'), 70),    # Sub-4:00: Top 30% (RunRepeat verified)
    (time_str_to_seconds('4:15:00'), 55),    # Sub-4:15: Top 45%
    (time_str_to_seconds('4:26:33'), 50),    # Median (RunRepeat verified US 2024)
    (time_str_to_seconds('4:45:00'), 40),    # Sub-4:45: Top 60%
    (time_str_to_seconds('5:00:00'), 30),    # Sub-5:00: Top 70%
    (time_str_to_seconds('5:30:00'), 18),    # Sub-5:30: Top 82%
    (time_str_to_seconds('6:00:00'), 10),    # Sub-6:00: Top 90%
]

# Legacy alias for backwards compatibility (5K thresholds)
PERCENTILE_THRESHOLDS = PERCENTILE_THRESHOLDS_5K


def get_percentile(time_seconds: int, distance: str = '5k') -> float:
    """
    Get approximate percentile for a given time and distance.
    Returns the percentage of runners you're faster than.

    Args:
        time_seconds: Time in seconds
        distance: One of '5k', '10k', 'half', 'marathon'
    """
    thresholds_map = {
        '5k': PERCENTILE_THRESHOLDS_5K,
        '10k': PERCENTILE_THRESHOLDS_10K,
        'half': PERCENTILE_THRESHOLDS_HALF,
        'marathon': PERCENTILE_THRESHOLDS_MARATHON,
    }

    thresholds = thresholds_map.get(distance.lower(), PERCENTILE_THRESHOLDS_5K)

    for threshold, percentile in thresholds:
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


def compare_to_distance_average(time_seconds: int, distance: str = '5k', gender: str = None) -> dict:
    """
    Compare a time to the global average for a distance.

    Args:
        time_seconds: Time in seconds
        distance: One of '5k', '10k', 'half', 'marathon'
        gender: Optional 'male' or 'female' for gender-specific comparison
    """
    dist_data = DISTANCE_AVERAGES.get(distance.lower())
    if not dist_data:
        return None

    if gender and gender.lower() in ['male', 'female']:
        avg_time = dist_data[gender.lower()]
        label = f"Global {dist_data['name']} Average ({gender.capitalize()})"
    else:
        avg_time = dist_data['overall']
        label = f"Global {dist_data['name']} Average"

    diff = avg_time - time_seconds
    faster = diff > 0

    return {
        'distance': distance,
        'name': label,
        'average_time': seconds_to_time_str(avg_time),
        'average_seconds': avg_time,
        'difference': abs(diff),
        'difference_str': seconds_to_time_str(abs(diff)),
        'faster': faster,
        'source': 'RunRepeat (107.9M race results)'
    }


def compare_to_all_distances(time_seconds: int, gender: str = None) -> list:
    """
    Compare a 5K time to equivalent times at other distances.
    Uses approximate pace scaling.
    """
    comparisons = []

    for distance_key, dist_data in DISTANCE_AVERAGES.items():
        if gender and gender.lower() in ['male', 'female']:
            avg_time = dist_data[gender.lower()]
        else:
            avg_time = dist_data['overall']

        comparisons.append({
            'distance': dist_data['name'],
            'average_time': seconds_to_time_str(avg_time),
            'average_seconds': avg_time,
            'source': 'RunRepeat'
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


def get_full_comparison(time_seconds: int, age: Optional[int] = None, gender: Optional[str] = None, distance: str = '5k') -> dict:
    """
    Get a complete comparison analysis for a given time.

    Args:
        time_seconds: Time in seconds
        age: Runner's age (optional)
        gender: 'male' or 'female' (optional)
        distance: One of '5k', '10k', 'half', 'marathon'
    """
    percentile = get_percentile(time_seconds, distance)

    # Use defaults if age/gender not provided
    effective_age = age if age else 35
    effective_gender = gender if gender else 'male'

    ability = get_ability_level(time_seconds, effective_age, effective_gender)

    # Get distance-specific comparison
    distance_comparison = compare_to_distance_average(time_seconds, distance, effective_gender)

    return {
        'time_seconds': time_seconds,
        'time_str': seconds_to_time_str(time_seconds),
        'percentile': percentile,
        'ability_level': ability,
        'rating_message': get_rating_message(percentile, ability),
        'parkrun_comparisons': compare_to_averages(time_seconds),
        'distance_comparison': distance_comparison,
        'all_distance_averages': compare_to_all_distances(time_seconds, effective_gender),
    }


# For testing
if __name__ == "__main__":
    print("=== 5K Test (25:00) ===")
    test_time = time_str_to_seconds("25:00")
    result = get_full_comparison(test_time, age=35, gender='male', distance='5k')
    print(f"Time: {result['time_str']}")
    print(f"Percentile: Faster than {result['percentile']}% of 5K runners")
    print(f"Ability Level: {result['ability_level']}")
    print(f"Rating: {result['rating_message']}")
    if result['distance_comparison']:
        print(f"vs {result['distance_comparison']['name']}: {result['distance_comparison']['average_time']}")

    print("\n=== Half Marathon Test (1:45:00) ===")
    test_time = time_str_to_seconds("1:45:00")
    result = get_full_comparison(test_time, age=35, gender='male', distance='half')
    print(f"Time: {result['time_str']}")
    print(f"Percentile: Faster than {result['percentile']}% of half marathon runners")
    if result['distance_comparison']:
        print(f"vs {result['distance_comparison']['name']}: {result['distance_comparison']['average_time']}")

    print("\n=== Marathon Test (4:00:00) ===")
    test_time = time_str_to_seconds("4:00:00")
    result = get_full_comparison(test_time, age=40, gender='female', distance='marathon')
    print(f"Time: {result['time_str']}")
    print(f"Percentile: Faster than {result['percentile']}% of marathon runners")
    if result['distance_comparison']:
        print(f"vs {result['distance_comparison']['name']}: {result['distance_comparison']['average_time']}")

    print("\n=== Global Distance Averages ===")
    for dist in compare_to_all_distances(0, 'male'):
        print(f"{dist['distance']}: {dist['average_time']} (Male avg)")
