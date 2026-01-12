"""
Multi-distance comparison data for running times.
Covers 5K, 10K, Half Marathon, and Marathon distances.
Data sourced from runninglevel.com and running research.
"""

from typing import Optional


def time_str_to_seconds(time_str: str) -> int:
    """Convert MM:SS or H:MM:SS to seconds."""
    parts = time_str.split(':')
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def seconds_to_time_str(seconds: int) -> str:
    """Convert seconds to MM:SS or H:MM:SS."""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


# Distance configurations
DISTANCES = {
    '5K': {
        'name': '5K',
        'meters': 5000,
        'global_avg': time_str_to_seconds('34:29'),
        'global_avg_male': time_str_to_seconds('33:08'),
        'global_avg_female': time_str_to_seconds('35:50'),
        'uk_avg': time_str_to_seconds('32:11'),
        'uk_avg_male': time_str_to_seconds('30:29'),
        'uk_avg_female': time_str_to_seconds('33:52'),
    },
    '10K': {
        'name': '10K',
        'meters': 10000,
        'global_avg': time_str_to_seconds('49:43'),
        'global_avg_male': time_str_to_seconds('46:43'),
        'global_avg_female': time_str_to_seconds('54:13'),
        'uk_avg': time_str_to_seconds('48:00'),
        'uk_avg_male': time_str_to_seconds('45:00'),
        'uk_avg_female': time_str_to_seconds('52:00'),
    },
    'Half Marathon': {
        'name': 'Half Marathon',
        'meters': 21097,
        'global_avg': time_str_to_seconds('1:50:15'),
        'global_avg_male': time_str_to_seconds('1:43:33'),
        'global_avg_female': time_str_to_seconds('2:00:12'),
        'uk_avg': time_str_to_seconds('1:48:00'),
        'uk_avg_male': time_str_to_seconds('1:41:00'),
        'uk_avg_female': time_str_to_seconds('1:58:00'),
    },
    'Marathon': {
        'name': 'Marathon',
        'meters': 42195,
        'global_avg': time_str_to_seconds('3:48:20'),
        'global_avg_male': time_str_to_seconds('3:34:56'),
        'global_avg_female': time_str_to_seconds('4:08:09'),
        'uk_avg': time_str_to_seconds('3:45:00'),
        'uk_avg_male': time_str_to_seconds('3:30:00'),
        'uk_avg_female': time_str_to_seconds('4:05:00'),
    },
    '10M': {
        'name': '10 Miles',
        'meters': 16093,
        'global_avg': time_str_to_seconds('1:25:00'),
        'global_avg_male': time_str_to_seconds('1:20:00'),
        'global_avg_female': time_str_to_seconds('1:32:00'),
        'uk_avg': time_str_to_seconds('1:22:00'),
        'uk_avg_male': time_str_to_seconds('1:18:00'),
        'uk_avg_female': time_str_to_seconds('1:30:00'),
    },
}

# Performance levels by distance, age, and gender
# Format: distance -> age -> gender -> {level: seconds}
# Based on realistic standards:
#   Elite: ~14:00 5K, ~30:00 10K, ~70:00 HM, ~2:15 Marathon (open male)
#   Advanced: Good club runner level
#   Intermediate: Regular club runner
#   Novice: Recreational runner
#   Beginner: Casual runner
PERFORMANCE_LEVELS = {
    '5K': {
        20: {
            'male': {'beginner': 1800, 'novice': 1440, 'intermediate': 1200, 'advanced': 1020, 'elite': 840},
            'female': {'beginner': 2040, 'novice': 1620, 'intermediate': 1350, 'advanced': 1140, 'elite': 960},
        },
        30: {
            'male': {'beginner': 1800, 'novice': 1440, 'intermediate': 1200, 'advanced': 1020, 'elite': 840},
            'female': {'beginner': 2040, 'novice': 1620, 'intermediate': 1350, 'advanced': 1140, 'elite': 960},
        },
        40: {
            'male': {'beginner': 1920, 'novice': 1530, 'intermediate': 1275, 'advanced': 1085, 'elite': 895},
            'female': {'beginner': 2160, 'novice': 1720, 'intermediate': 1435, 'advanced': 1210, 'elite': 1020},
        },
        50: {
            'male': {'beginner': 2070, 'novice': 1656, 'intermediate': 1380, 'advanced': 1175, 'elite': 970},
            'female': {'beginner': 2345, 'novice': 1870, 'intermediate': 1555, 'advanced': 1315, 'elite': 1105},
        },
        55: {
            'male': {'beginner': 2175, 'novice': 1740, 'intermediate': 1450, 'advanced': 1235, 'elite': 1020},
            'female': {'beginner': 2460, 'novice': 1960, 'intermediate': 1635, 'advanced': 1380, 'elite': 1160},
        },
        60: {
            'male': {'beginner': 2295, 'novice': 1835, 'intermediate': 1530, 'advanced': 1300, 'elite': 1075},
            'female': {'beginner': 2600, 'novice': 2070, 'intermediate': 1725, 'advanced': 1460, 'elite': 1225},
        },
    },
    '10K': {
        20: {
            'male': {'beginner': 3600, 'novice': 3000, 'intermediate': 2520, 'advanced': 2160, 'elite': 1800},
            'female': {'beginner': 4080, 'novice': 3400, 'intermediate': 2850, 'advanced': 2430, 'elite': 2040},
        },
        30: {
            'male': {'beginner': 3600, 'novice': 3000, 'intermediate': 2520, 'advanced': 2160, 'elite': 1800},
            'female': {'beginner': 4080, 'novice': 3400, 'intermediate': 2850, 'advanced': 2430, 'elite': 2040},
        },
        40: {
            'male': {'beginner': 3840, 'novice': 3195, 'intermediate': 2680, 'advanced': 2300, 'elite': 1920},
            'female': {'beginner': 4340, 'novice': 3620, 'intermediate': 3035, 'advanced': 2590, 'elite': 2170},
        },
        50: {
            'male': {'beginner': 4140, 'novice': 3450, 'intermediate': 2900, 'advanced': 2485, 'elite': 2070},
            'female': {'beginner': 4700, 'novice': 3910, 'intermediate': 3280, 'advanced': 2795, 'elite': 2345},
        },
        55: {
            'male': {'beginner': 4350, 'novice': 3625, 'intermediate': 3045, 'advanced': 2610, 'elite': 2175},
            'female': {'beginner': 4930, 'novice': 4110, 'intermediate': 3445, 'advanced': 2935, 'elite': 2465},
        },
        60: {
            'male': {'beginner': 4590, 'novice': 3825, 'intermediate': 3210, 'advanced': 2755, 'elite': 2295},
            'female': {'beginner': 5200, 'novice': 4335, 'intermediate': 3635, 'advanced': 3100, 'elite': 2600},
        },
    },
    'Half Marathon': {
        20: {
            'male': {'beginner': 7800, 'novice': 6600, 'intermediate': 5700, 'advanced': 4920, 'elite': 4200},
            'female': {'beginner': 8820, 'novice': 7440, 'intermediate': 6420, 'advanced': 5520, 'elite': 4740},
        },
        30: {
            'male': {'beginner': 7800, 'novice': 6600, 'intermediate': 5700, 'advanced': 4920, 'elite': 4200},
            'female': {'beginner': 8820, 'novice': 7440, 'intermediate': 6420, 'advanced': 5520, 'elite': 4740},
        },
        40: {
            'male': {'beginner': 8310, 'novice': 7030, 'intermediate': 6070, 'advanced': 5240, 'elite': 4475},
            'female': {'beginner': 9390, 'novice': 7925, 'intermediate': 6840, 'advanced': 5880, 'elite': 5050},
        },
        50: {
            'male': {'beginner': 8970, 'novice': 7590, 'intermediate': 6555, 'advanced': 5660, 'elite': 4620},
            'female': {'beginner': 10140, 'novice': 8565, 'intermediate': 7390, 'advanced': 6350, 'elite': 5220},
        },
        55: {
            'male': {'beginner': 9420, 'novice': 7970, 'intermediate': 6880, 'advanced': 5100, 'elite': 4710},
            'female': {'beginner': 10650, 'novice': 9000, 'intermediate': 7765, 'advanced': 5760, 'elite': 5325},
        },
        60: {
            'male': {'beginner': 9945, 'novice': 8415, 'intermediate': 7265, 'advanced': 5385, 'elite': 4970},
            'female': {'beginner': 11240, 'novice': 9500, 'intermediate': 8200, 'advanced': 6090, 'elite': 5625},
        },
    },
    'Marathon': {
        20: {
            'male': {'beginner': 16200, 'novice': 13500, 'intermediate': 11700, 'advanced': 9900, 'elite': 8100},
            'female': {'beginner': 18360, 'novice': 15300, 'intermediate': 13260, 'advanced': 11220, 'elite': 9180},
        },
        30: {
            'male': {'beginner': 16200, 'novice': 13500, 'intermediate': 11700, 'advanced': 9900, 'elite': 8100},
            'female': {'beginner': 18360, 'novice': 15300, 'intermediate': 13260, 'advanced': 11220, 'elite': 9180},
        },
        40: {
            'male': {'beginner': 17265, 'novice': 14385, 'intermediate': 12465, 'advanced': 10545, 'elite': 8630},
            'female': {'beginner': 19555, 'novice': 16295, 'intermediate': 14120, 'advanced': 11955, 'elite': 9780},
        },
        50: {
            'male': {'beginner': 18630, 'novice': 15525, 'intermediate': 13455, 'advanced': 11385, 'elite': 9315},
            'female': {'beginner': 21100, 'novice': 17595, 'intermediate': 15250, 'advanced': 12905, 'elite': 10560},
        },
        55: {
            'male': {'beginner': 19560, 'novice': 16300, 'intermediate': 14125, 'advanced': 11950, 'elite': 9780},
            'female': {'beginner': 22155, 'novice': 18475, 'intermediate': 16010, 'advanced': 13550, 'elite': 11085},
        },
        60: {
            'male': {'beginner': 20655, 'novice': 17215, 'intermediate': 14915, 'advanced': 12620, 'elite': 10330},
            'female': {'beginner': 23395, 'novice': 19510, 'intermediate': 16910, 'advanced': 14315, 'elite': 11710},
        },
    },
    '10M': {
        20: {
            'male': {'beginner': 6000, 'novice': 5100, 'intermediate': 4440, 'advanced': 3840, 'elite': 3300},
            'female': {'beginner': 6780, 'novice': 5760, 'intermediate': 5010, 'advanced': 4335, 'elite': 3725},
        },
        30: {
            'male': {'beginner': 6000, 'novice': 5100, 'intermediate': 4440, 'advanced': 3840, 'elite': 3300},
            'female': {'beginner': 6780, 'novice': 5760, 'intermediate': 5010, 'advanced': 4335, 'elite': 3725},
        },
        40: {
            'male': {'beginner': 6390, 'novice': 5430, 'intermediate': 4725, 'advanced': 4090, 'elite': 3515},
            'female': {'beginner': 7220, 'novice': 6135, 'intermediate': 5335, 'advanced': 4620, 'elite': 3970},
        },
        50: {
            'male': {'beginner': 6900, 'novice': 5865, 'intermediate': 5100, 'advanced': 4415, 'elite': 3795},
            'female': {'beginner': 7800, 'novice': 6625, 'intermediate': 5760, 'advanced': 4985, 'elite': 4290},
        },
        55: {
            'male': {'beginner': 7245, 'novice': 6155, 'intermediate': 5355, 'advanced': 4635, 'elite': 3985},
            'female': {'beginner': 8190, 'novice': 6955, 'intermediate': 6050, 'advanced': 5235, 'elite': 4505},
        },
        60: {
            'male': {'beginner': 7650, 'novice': 6500, 'intermediate': 5655, 'advanced': 4895, 'elite': 4205},
            'female': {'beginner': 8645, 'novice': 7345, 'intermediate': 6390, 'advanced': 5530, 'elite': 4755},
        },
    },
}

# Percentile thresholds by distance (time in seconds -> percentile)
PERCENTILE_THRESHOLDS = {
    '5K': [
        (900, 99.9), (1020, 99), (1080, 98), (1140, 95), (1200, 90),
        (1260, 85), (1320, 80), (1380, 75), (1440, 70), (1500, 65),
        (1560, 60), (1680, 55), (1740, 50), (1800, 47), (1920, 42),
        (2100, 35), (2280, 28), (2400, 23), (2700, 15), (3000, 10),
        (3300, 6), (3600, 3),
    ],
    '10K': [
        (1920, 99.9), (2160, 99), (2280, 98), (2400, 95), (2520, 90),
        (2700, 85), (2880, 80), (3000, 75), (3120, 70), (3240, 65),
        (3360, 60), (3480, 55), (3600, 50), (3720, 47), (3900, 42),
        (4200, 35), (4500, 28), (4800, 23), (5400, 15), (6000, 10),
        (6600, 6), (7200, 3),
    ],
    'Half Marathon': [
        (4200, 99.9), (4680, 99), (4920, 98), (5220, 95), (5520, 90),
        (5880, 85), (6240, 80), (6540, 75), (6840, 70), (7140, 65),
        (7440, 60), (7740, 55), (8040, 50), (8400, 47), (8820, 42),
        (9600, 35), (10200, 28), (10800, 23), (12000, 15), (13200, 10),
        (14400, 6), (16200, 3),
    ],
    'Marathon': [
        (8400, 99.9), (9300, 99), (9900, 98), (10500, 95), (11100, 90),
        (11820, 85), (12540, 80), (13200, 75), (13860, 70), (14400, 65),
        (14940, 60), (15480, 55), (16020, 50), (16680, 47), (17400, 42),
        (18600, 35), (19800, 28), (21000, 23), (23400, 15), (25200, 10),
        (27000, 6), (30600, 3),
    ],
    '10M': [
        (3300, 99.9), (3660, 99), (3900, 98), (4140, 95), (4380, 90),
        (4680, 85), (4980, 80), (5220, 75), (5460, 70), (5700, 65),
        (5940, 60), (6180, 55), (6420, 50), (6660, 47), (6960, 42),
        (7500, 35), (8100, 28), (8640, 23), (9600, 15), (10800, 10),
        (12000, 6), (13500, 3),
    ],
}


def get_percentile(time_seconds: int, distance: str) -> float:
    """Get approximate percentile for a given time at a specific distance."""
    thresholds = PERCENTILE_THRESHOLDS.get(distance, PERCENTILE_THRESHOLDS['5K'])

    for threshold, percentile in thresholds:
        if time_seconds <= threshold:
            return percentile

    return 1.0


def get_ability_level(time_seconds: int, distance: str, age: int = 35, gender: str = 'male') -> str:
    """Determine ability level based on time, distance, age, and gender."""
    if distance not in PERFORMANCE_LEVELS:
        return 'intermediate'

    # Find closest age bracket
    ages = sorted(PERFORMANCE_LEVELS[distance].keys())
    closest_age = min(ages, key=lambda x: abs(x - age))

    gender_key = gender.lower() if gender else 'male'
    if gender_key not in ['male', 'female']:
        gender_key = 'male'

    thresholds = PERFORMANCE_LEVELS[distance][closest_age].get(gender_key, PERFORMANCE_LEVELS[distance][closest_age]['male'])

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


def get_rating_message(percentile: float, distance: str) -> str:
    """Generate a rating message based on performance."""
    distance_name = DISTANCES.get(distance, {}).get('name', distance)

    if percentile >= 99:
        return f"Incredible! You're among the fastest {distance_name} runners!"
    elif percentile >= 95:
        return f"Outstanding! Elite-level {distance_name} performance!"
    elif percentile >= 90:
        return f"Excellent! Faster than 90% of {distance_name} runners!"
    elif percentile >= 80:
        return f"Great {distance_name} time! Faster than 80% of runners!"
    elif percentile >= 70:
        return f"Well done! Faster than most {distance_name} runners!"
    elif percentile >= 50:
        return f"Good {distance_name} time! Faster than average!"
    elif percentile >= 30:
        return f"Solid {distance_name} effort! Keep training!"
    else:
        return f"You completed the {distance_name}! Great achievement!"


def compare_to_averages(time_seconds: int, distance: str, gender: Optional[str] = None) -> list:
    """Compare a time to various averages for the distance."""
    if distance not in DISTANCES:
        return []

    dist_data = DISTANCES[distance]
    comparisons = []

    # Compare to global average
    diff = dist_data['global_avg'] - time_seconds
    comparisons.append({
        'name': f'Global {dist_data["name"]} Average',
        'benchmark_seconds': dist_data['global_avg'],
        'benchmark_time': seconds_to_time_str(dist_data['global_avg']),
        'difference': abs(diff),
        'difference_str': seconds_to_time_str(abs(diff)),
        'faster': diff > 0,
    })

    # Compare to UK average
    diff = dist_data['uk_avg'] - time_seconds
    comparisons.append({
        'name': f'UK {dist_data["name"]} Average',
        'benchmark_seconds': dist_data['uk_avg'],
        'benchmark_time': seconds_to_time_str(dist_data['uk_avg']),
        'difference': abs(diff),
        'difference_str': seconds_to_time_str(abs(diff)),
        'faster': diff > 0,
    })

    # Gender-specific if provided
    if gender:
        gender_key = gender.lower()
        if gender_key == 'male':
            avg_key = 'global_avg_male'
            label = f'Global Male {dist_data["name"]} Average'
        else:
            avg_key = 'global_avg_female'
            label = f'Global Female {dist_data["name"]} Average'

        diff = dist_data[avg_key] - time_seconds
        comparisons.append({
            'name': label,
            'benchmark_seconds': dist_data[avg_key],
            'benchmark_time': seconds_to_time_str(dist_data[avg_key]),
            'difference': abs(diff),
            'difference_str': seconds_to_time_str(abs(diff)),
            'faster': diff > 0,
        })

    return comparisons


def get_distance_comparison(time_seconds: int, distance: str, age: Optional[int] = None, gender: Optional[str] = None) -> dict:
    """Get full comparison data for a specific distance and time."""
    effective_age = age if age else 35
    effective_gender = gender if gender else 'male'

    percentile = get_percentile(time_seconds, distance)
    ability = get_ability_level(time_seconds, distance, effective_age, effective_gender)

    return {
        'distance': distance,
        'distance_name': DISTANCES.get(distance, {}).get('name', distance),
        'time_seconds': time_seconds,
        'time_str': seconds_to_time_str(time_seconds),
        'percentile': percentile,
        'ability_level': ability,
        'rating_message': get_rating_message(percentile, distance),
        'comparisons': compare_to_averages(time_seconds, distance, gender),
    }


def get_all_distance_comparisons(pbs: dict, age: Optional[int] = None, gender: Optional[str] = None) -> dict:
    """
    Get comparison data for all distances with PBs.

    Args:
        pbs: Dict of distance -> {'seconds': int, 'time': str}
        age: Athlete's age
        gender: Athlete's gender

    Returns:
        Dict with comparison data for each distance
    """
    results = {}

    for distance, pb_data in pbs.items():
        if pb_data and pb_data.get('seconds'):
            results[distance] = get_distance_comparison(
                pb_data['seconds'],
                distance,
                age,
                gender
            )

    return results


# For testing
if __name__ == "__main__":
    # Test with sample times
    pbs = {
        '5K': {'seconds': time_str_to_seconds('18:16'), 'time': '18:16'},
        '10K': {'seconds': time_str_to_seconds('39:43'), 'time': '39:43'},
        'Half Marathon': {'seconds': time_str_to_seconds('1:23:27'), 'time': '1:23:27'},
        'Marathon': {'seconds': time_str_to_seconds('2:55:42'), 'time': '2:55:42'},
    }

    results = get_all_distance_comparisons(pbs, age=55, gender='male')

    for distance, data in results.items():
        print(f"\n{distance}: {data['time_str']}")
        print(f"  Percentile: {data['percentile']}%")
        print(f"  Level: {data['ability_level']}")
        print(f"  {data['rating_message']}")
