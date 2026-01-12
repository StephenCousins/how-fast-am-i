"""
Age Grading Calculator using 2023 WMA Age Grading Factors.

Age grading allows comparison of performances across different ages and genders
by calculating what percentage of the "open class standard" (approximately world
record level) a performance represents, adjusted for age.

Formula: Age Grade % = (Open Standard × Age Factor) / Actual Time × 100
"""

from typing import Optional, Tuple


# 2023 WMA Open Class Standards (in seconds)
# These represent approximately world record level performances
OPEN_STANDARDS = {
    'male': {
        '5K': 755,        # 12:35
        '10K': 1571,      # 26:11
        'Half Marathon': 3451,  # 57:31
        'Marathon': 7235,      # 2:00:35
        '10M': 2736,      # 45:36
    },
    'female': {
        '5K': 846,        # 14:06
        '10K': 1741,      # 29:01
        'Half Marathon': 3772,  # 1:02:52
        'Marathon': 7913,      # 2:11:53
        '10M': 3030,      # 50:30
    }
}


# 2023 WMA Age Factors by gender, event, and age
# Factor of 1.0 means no adjustment needed (peak performance age)
# Lower factors mean more adjustment credit for older ages

WMA_FACTORS = {
    'female': {
        '5K': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 1.0000,
            35: 0.9974, 36: 0.9904, 37: 0.9833, 38: 0.9761, 39: 0.9689,
            40: 0.9615, 41: 0.9541, 42: 0.9467, 43: 0.9392, 44: 0.9316,
            45: 0.9239, 46: 0.9162, 47: 0.9084, 48: 0.9006, 49: 0.8926,
            50: 0.8847, 51: 0.8766, 52: 0.8685, 53: 0.8603, 54: 0.8521,
            55: 0.8438, 56: 0.8355, 57: 0.8271, 58: 0.8186, 59: 0.8101,
            60: 0.8015, 61: 0.7929, 62: 0.7842, 63: 0.7755, 64: 0.7667,
            65: 0.7578, 66: 0.7489, 67: 0.7399, 68: 0.7309, 69: 0.7219,
            70: 0.7128, 71: 0.7036, 72: 0.6944, 73: 0.6851, 74: 0.6758,
            75: 0.6665, 76: 0.6571, 77: 0.6476, 78: 0.6381, 79: 0.6286,
            80: 0.6190, 81: 0.6094, 82: 0.5997, 83: 0.5893, 84: 0.5783,
            85: 0.5665, 86: 0.5541, 87: 0.5410, 88: 0.5272, 89: 0.5127,
            90: 0.4975, 91: 0.4816, 92: 0.4650, 93: 0.4478, 94: 0.4299,
            95: 0.4112, 96: 0.3919, 97: 0.3719, 98: 0.3513, 99: 0.3299,
            100: 0.3079,
        },
        '10K': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 0.9937,
            35: 0.9869, 36: 0.9801, 37: 0.9731, 38: 0.9661, 39: 0.9591,
            40: 0.9519, 41: 0.9447, 42: 0.9374, 43: 0.9301, 44: 0.9227,
            45: 0.9152, 46: 0.9077, 47: 0.9001, 48: 0.8925, 49: 0.8848,
            50: 0.8770, 51: 0.8692, 52: 0.8613, 53: 0.8533, 54: 0.8453,
            55: 0.8373, 56: 0.8291, 57: 0.8210, 58: 0.8127, 59: 0.8045,
            60: 0.7961, 61: 0.7877, 62: 0.7793, 63: 0.7708, 64: 0.7623,
            65: 0.7537, 66: 0.7450, 67: 0.7363, 68: 0.7276, 69: 0.7188,
            70: 0.7100, 71: 0.7011, 72: 0.6922, 73: 0.6832, 74: 0.6742,
            75: 0.6651, 76: 0.6560, 77: 0.6468, 78: 0.6376, 79: 0.6284,
            80: 0.6191, 81: 0.6098, 82: 0.6004, 83: 0.5903, 84: 0.5795,
            85: 0.5679, 86: 0.5556, 87: 0.5425, 88: 0.5287, 89: 0.5142,
            90: 0.4990, 91: 0.4830, 92: 0.4662, 93: 0.4488, 94: 0.4306,
            95: 0.4116, 96: 0.3920, 97: 0.3716, 98: 0.3505, 99: 0.3286,
            100: 0.3060,
        },
        'Half Marathon': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 0.9935, 34: 0.9869,
            35: 0.9802, 36: 0.9734, 37: 0.9666, 38: 0.9596, 39: 0.9526,
            40: 0.9455, 41: 0.9384, 42: 0.9311, 43: 0.9238, 44: 0.9164,
            45: 0.9090, 46: 0.9014, 47: 0.8938, 48: 0.8862, 49: 0.8784,
            50: 0.8706, 51: 0.8627, 52: 0.8548, 53: 0.8468, 54: 0.8387,
            55: 0.8306, 56: 0.8224, 57: 0.8141, 58: 0.8058, 59: 0.7974,
            60: 0.7889, 61: 0.7804, 62: 0.7718, 63: 0.7632, 64: 0.7545,
            65: 0.7457, 66: 0.7369, 67: 0.7280, 68: 0.7191, 69: 0.7101,
            70: 0.7011, 71: 0.6920, 72: 0.6828, 73: 0.6736, 74: 0.6644,
            75: 0.6551, 76: 0.6457, 77: 0.6363, 78: 0.6268, 79: 0.6173,
            80: 0.6078, 81: 0.5982, 82: 0.5879, 83: 0.5769, 84: 0.5653,
            85: 0.5530, 86: 0.5401, 87: 0.5265, 88: 0.5122, 89: 0.4972,
            90: 0.4816, 91: 0.4653, 92: 0.4484, 93: 0.4307, 94: 0.4125,
            95: 0.3935, 96: 0.3739, 97: 0.3536, 98: 0.3327, 99: 0.3111,
            100: 0.2888,
        },
        'Marathon': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 1.0000,
            35: 0.9982, 36: 0.9918, 37: 0.9854, 38: 0.9789, 39: 0.9722,
            40: 0.9654, 41: 0.9585, 42: 0.9515, 43: 0.9444, 44: 0.9371,
            45: 0.9298, 46: 0.9223, 47: 0.9148, 48: 0.9071, 49: 0.8993,
            50: 0.8915, 51: 0.8835, 52: 0.8754, 53: 0.8672, 54: 0.8590,
            55: 0.8506, 56: 0.8421, 57: 0.8336, 58: 0.8249, 59: 0.8162,
            60: 0.8073, 61: 0.7984, 62: 0.7894, 63: 0.7803, 64: 0.7711,
            65: 0.7618, 66: 0.7524, 67: 0.7430, 68: 0.7335, 69: 0.7239,
            70: 0.7142, 71: 0.7044, 72: 0.6946, 73: 0.6846, 74: 0.6746,
            75: 0.6646, 76: 0.6544, 77: 0.6442, 78: 0.6339, 79: 0.6235,
            80: 0.6131, 81: 0.6025, 82: 0.5914, 83: 0.5795, 84: 0.5670,
            85: 0.5538, 86: 0.5400, 87: 0.5254, 88: 0.5103, 89: 0.4944,
            90: 0.4779, 91: 0.4608, 92: 0.4429, 93: 0.4245, 94: 0.4053,
            95: 0.3855, 96: 0.3651, 97: 0.3439, 98: 0.3222, 99: 0.2997,
            100: 0.2767,
        },
    },
    'male': {
        '5K': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 1.0000,
            35: 1.0000, 36: 1.0000, 37: 0.9943, 38: 0.9863, 39: 0.9782,
            40: 0.9701, 41: 0.9621, 42: 0.9540, 43: 0.9460, 44: 0.9380,
            45: 0.9299, 46: 0.9219, 47: 0.9139, 48: 0.9059, 49: 0.8980,
            50: 0.8900, 51: 0.8820, 52: 0.8740, 53: 0.8661, 54: 0.8582,
            55: 0.8502, 56: 0.8423, 57: 0.8344, 58: 0.8265, 59: 0.8185,
            60: 0.8106, 61: 0.8028, 62: 0.7949, 63: 0.7870, 64: 0.7791,
            65: 0.7713, 66: 0.7634, 67: 0.7556, 68: 0.7477, 69: 0.7399,
            70: 0.7321, 71: 0.7242, 72: 0.7164, 73: 0.7086, 74: 0.7008,
            75: 0.6930, 76: 0.6852, 77: 0.6775, 78: 0.6697, 79: 0.6619,
            80: 0.6541, 81: 0.6456, 82: 0.6362, 83: 0.6261, 84: 0.6151,
            85: 0.6034, 86: 0.5908, 87: 0.5775, 88: 0.5633, 89: 0.5484,
            90: 0.5326, 91: 0.5161, 92: 0.4987, 93: 0.4806, 94: 0.4617,
            95: 0.4419, 96: 0.4214, 97: 0.4000, 98: 0.3779, 99: 0.3550,
            100: 0.3313,
        },
        '10K': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 0.9973,
            35: 0.9897, 36: 0.9822, 37: 0.9747, 38: 0.9672, 39: 0.9597,
            40: 0.9523, 41: 0.9449, 42: 0.9375, 43: 0.9301, 44: 0.9228,
            45: 0.9155, 46: 0.9082, 47: 0.9009, 48: 0.8937, 49: 0.8865,
            50: 0.8793, 51: 0.8722, 52: 0.8650, 53: 0.8579, 54: 0.8509,
            55: 0.8438, 56: 0.8368, 57: 0.8298, 58: 0.8228, 59: 0.8158,
            60: 0.8089, 61: 0.8019, 62: 0.7950, 63: 0.7882, 64: 0.7813,
            65: 0.7745, 66: 0.7677, 67: 0.7609, 68: 0.7541, 69: 0.7474,
            70: 0.7407, 71: 0.7340, 72: 0.7273, 73: 0.7206, 74: 0.7140,
            75: 0.7073, 76: 0.7007, 77: 0.6942, 78: 0.6868, 79: 0.6787,
            80: 0.6698, 81: 0.6601, 82: 0.6496, 83: 0.6383, 84: 0.6263,
            85: 0.6135, 86: 0.5999, 87: 0.5856, 88: 0.5704, 89: 0.5545,
            90: 0.5378, 91: 0.5203, 92: 0.5021, 93: 0.4830, 94: 0.4632,
            95: 0.4426, 96: 0.4213, 97: 0.3991, 98: 0.3762, 99: 0.3524,
            100: 0.3279,
        },
        'Half Marathon': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 0.9970,
            35: 0.9914, 36: 0.9857, 37: 0.9800, 38: 0.9742, 39: 0.9683,
            40: 0.9624, 41: 0.9564, 42: 0.9503, 43: 0.9442, 44: 0.9380,
            45: 0.9317, 46: 0.9254, 47: 0.9190, 48: 0.9126, 49: 0.9061,
            50: 0.8996, 51: 0.8930, 52: 0.8864, 53: 0.8797, 54: 0.8730,
            55: 0.8662, 56: 0.8594, 57: 0.8526, 58: 0.8457, 59: 0.8387,
            60: 0.8317, 61: 0.8247, 62: 0.8176, 63: 0.8105, 64: 0.8034,
            65: 0.7962, 66: 0.7890, 67: 0.7818, 68: 0.7745, 69: 0.7672,
            70: 0.7600, 71: 0.7534, 72: 0.7468, 73: 0.7396, 74: 0.7318,
            75: 0.7233, 76: 0.7142, 77: 0.7044, 78: 0.6941, 79: 0.6831,
            80: 0.6715, 81: 0.6592, 82: 0.6463, 83: 0.6328, 84: 0.6187,
            85: 0.6039, 86: 0.5885, 87: 0.5725, 88: 0.5558, 89: 0.5385,
            90: 0.5206, 91: 0.5021, 92: 0.4829, 93: 0.4631, 94: 0.4426,
            95: 0.4216, 96: 0.3999, 97: 0.3776, 98: 0.3546, 99: 0.3310,
            100: 0.3068,
        },
        'Marathon': {
            30: 1.0000, 31: 1.0000, 32: 1.0000, 33: 1.0000, 34: 1.0000,
            35: 1.0000, 36: 1.0000, 37: 1.0000, 38: 0.9947, 39: 0.9876,
            40: 0.9804, 41: 0.9733, 42: 0.9661, 43: 0.9589, 44: 0.9517,
            45: 0.9445, 46: 0.9372, 47: 0.9299, 48: 0.9226, 49: 0.9153,
            50: 0.9079, 51: 0.9005, 52: 0.8931, 53: 0.8857, 54: 0.8783,
            55: 0.8708, 56: 0.8633, 57: 0.8558, 58: 0.8483, 59: 0.8407,
            60: 0.8331, 61: 0.8255, 62: 0.8179, 63: 0.8103, 64: 0.8026,
            65: 0.7950, 66: 0.7873, 67: 0.7796, 68: 0.7718, 69: 0.7641,
            70: 0.7563, 71: 0.7485, 72: 0.7407, 73: 0.7329, 74: 0.7250,
            75: 0.7165, 76: 0.7074, 77: 0.6976, 78: 0.6871, 79: 0.6760,
            80: 0.6643, 81: 0.6519, 82: 0.6388, 83: 0.6251, 84: 0.6108,
            85: 0.5958, 86: 0.5801, 87: 0.5638, 88: 0.5469, 89: 0.5293,
            90: 0.5110, 91: 0.4921, 92: 0.4726, 93: 0.4524, 94: 0.4316,
            95: 0.4101, 96: 0.3879, 97: 0.3651, 98: 0.3417, 99: 0.3176,
            100: 0.2929,
        },
    },
}

# Add 10M factors (interpolated from 10K and Half Marathon)
for gender in ['male', 'female']:
    WMA_FACTORS[gender]['10M'] = {}
    for age in range(30, 101):
        # 10 miles is between 10K and Half Marathon - use weighted average
        factor_10k = WMA_FACTORS[gender]['10K'].get(age, 0.5)
        factor_hm = WMA_FACTORS[gender]['Half Marathon'].get(age, 0.5)
        # 10M is closer to HM than 10K in terms of energy systems
        WMA_FACTORS[gender]['10M'][age] = factor_10k * 0.4 + factor_hm * 0.6


def get_age_factor(age: int, distance: str, gender: str) -> float:
    """
    Get the WMA age factor for a given age, distance, and gender.

    Args:
        age: Runner's age (will be clamped to 30-100)
        distance: One of '5K', '10K', '10M', 'Half Marathon', 'Marathon'
        gender: 'male' or 'female'

    Returns:
        Age factor (1.0 = no adjustment, lower = more age credit)
    """
    gender = gender.lower()
    if gender not in WMA_FACTORS:
        gender = 'male'

    if distance not in WMA_FACTORS[gender]:
        return 1.0

    # Clamp age to valid range
    age = max(30, min(100, age))

    factors = WMA_FACTORS[gender][distance]
    return factors.get(age, 1.0)


def get_open_standard(distance: str, gender: str) -> int:
    """
    Get the open class standard time for a distance and gender.

    Returns:
        Time in seconds
    """
    gender = gender.lower()
    if gender not in OPEN_STANDARDS:
        gender = 'male'

    return OPEN_STANDARDS[gender].get(distance, 0)


def calculate_age_grade(
    time_seconds: int,
    distance: str,
    age: int,
    gender: str
) -> Tuple[float, int]:
    """
    Calculate the age grade percentage for a performance.

    Args:
        time_seconds: Actual finish time in seconds
        distance: One of '5K', '10K', '10M', 'Half Marathon', 'Marathon'
        age: Runner's age
        gender: 'male' or 'female'

    Returns:
        Tuple of (age_grade_percentage, age_graded_time_seconds)

    Age Grade Formula:
        Age Grade % = (Open Standard × Age Factor) / Actual Time × 100

    This tells you what percentage of the age-adjusted world record you ran.
    """
    open_standard = get_open_standard(distance, gender)
    age_factor = get_age_factor(age, distance, gender)

    if open_standard == 0 or time_seconds == 0:
        return 0.0, 0

    # Age-graded time = actual time adjusted for age
    # (what time would you have run if you were at peak age?)
    age_graded_time = int(time_seconds * age_factor)

    # Age grade percentage
    age_grade = (open_standard / age_graded_time) * 100

    return round(age_grade, 1), age_graded_time


def get_age_grade_category(age_grade: float) -> Tuple[str, str]:
    """
    Get the performance category for an age grade percentage.

    Returns:
        Tuple of (category_name, description)
    """
    if age_grade >= 90:
        return 'world_class', 'World Class'
    elif age_grade >= 80:
        return 'national', 'National Class'
    elif age_grade >= 70:
        return 'regional', 'Regional Class'
    elif age_grade >= 60:
        return 'club', 'Club Runner'
    elif age_grade >= 50:
        return 'recreational', 'Recreational'
    else:
        return 'beginner', 'Beginner'


def seconds_to_time_str(seconds: int) -> str:
    """Convert seconds to MM:SS or H:MM:SS format."""
    if seconds >= 3600:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"


# For testing
if __name__ == "__main__":
    # Test with sample times (Stephen Cousins V55 Male)
    test_cases = [
        ('5K', 18*60+16, 55, 'male'),      # 18:16
        ('10K', 39*60+43, 55, 'male'),     # 39:43
        ('Half Marathon', 83*60+27, 55, 'male'),  # 1:23:27
        ('Marathon', 175*60+42, 55, 'male'),      # 2:55:42
    ]

    print("Age Grading Test Results:")
    print("-" * 70)

    for distance, time_sec, age, gender in test_cases:
        ag_pct, ag_time = calculate_age_grade(time_sec, distance, age, gender)
        category, cat_name = get_age_grade_category(ag_pct)

        print(f"{distance}: {seconds_to_time_str(time_sec)}")
        print(f"  Age Grade: {ag_pct}% ({cat_name})")
        print(f"  Age-Graded Time: {seconds_to_time_str(ag_time)}")
        print()
