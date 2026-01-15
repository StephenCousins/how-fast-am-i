"""
Tests for age grading calculations.
"""

import pytest
from age_grading import (
    get_age_factor,
    get_open_standard,
    calculate_age_grade,
    get_age_grade_category,
    OPEN_STANDARDS,
    WMA_FACTORS,
)


class TestGetAgeFactor:
    """Tests for get_age_factor function."""

    # Basic factor retrieval
    def test_male_5k_age_30(self):
        """Age 30 should have factor of 1.0 (peak performance)."""
        factor = get_age_factor(30, '5K', 'male')
        assert factor == 1.0

    def test_male_5k_age_55(self):
        """V55 male 5K factor from WMA tables."""
        factor = get_age_factor(55, '5K', 'male')
        assert factor == 0.8502

    def test_female_5k_age_55(self):
        """V55 female 5K factor from WMA tables."""
        factor = get_age_factor(55, '5K', 'female')
        assert factor == 0.8438

    def test_male_marathon_age_40(self):
        """V40 male marathon factor."""
        factor = get_age_factor(40, 'Marathon', 'male')
        assert factor == 0.9804

    # Age clamping
    def test_age_below_30_clamped(self):
        """Ages below 30 should be clamped to 30."""
        factor = get_age_factor(25, '5K', 'male')
        assert factor == 1.0  # Same as age 30

    def test_age_above_100_clamped(self):
        """Ages above 100 should be clamped to 100."""
        factor = get_age_factor(105, '5K', 'male')
        assert factor == 0.3313  # Same as age 100

    # Gender handling
    def test_gender_case_insensitive(self):
        """Gender should be case-insensitive."""
        factor_lower = get_age_factor(55, '5K', 'male')
        factor_upper = get_age_factor(55, '5K', 'MALE')
        factor_mixed = get_age_factor(55, '5K', 'Male')
        assert factor_lower == factor_upper == factor_mixed

    def test_invalid_gender_defaults_to_male(self):
        """Invalid gender should default to male."""
        factor = get_age_factor(55, '5K', 'unknown')
        assert factor == get_age_factor(55, '5K', 'male')

    # Unknown distance
    def test_unknown_distance_returns_1(self):
        """Unknown distance should return factor of 1.0."""
        factor = get_age_factor(55, 'Unknown Distance', 'male')
        assert factor == 1.0

    # All supported distances
    def test_all_distances_have_factors(self):
        """All supported distances should return valid factors."""
        distances = ['5K', '10K', '10M', 'Half Marathon', 'Marathon']
        for distance in distances:
            factor = get_age_factor(50, distance, 'male')
            assert 0 < factor <= 1.0, f"Invalid factor for {distance}"

    # Factor decreases with age
    def test_factor_decreases_with_age(self):
        """Age factor should decrease as age increases."""
        factor_40 = get_age_factor(40, '5K', 'male')
        factor_50 = get_age_factor(50, '5K', 'male')
        factor_60 = get_age_factor(60, '5K', 'male')
        assert factor_40 > factor_50 > factor_60


class TestGetOpenStandard:
    """Tests for get_open_standard function."""

    # Male standards
    def test_male_5k_standard(self):
        """Male 5K open standard is 12:35 (755 seconds)."""
        standard = get_open_standard('5K', 'male')
        assert standard == 755

    def test_male_10k_standard(self):
        """Male 10K open standard."""
        standard = get_open_standard('10K', 'male')
        assert standard == 1571

    def test_male_half_marathon_standard(self):
        """Male half marathon open standard."""
        standard = get_open_standard('Half Marathon', 'male')
        assert standard == 3451

    def test_male_marathon_standard(self):
        """Male marathon open standard is ~2:00:35."""
        standard = get_open_standard('Marathon', 'male')
        assert standard == 7235

    # Female standards
    def test_female_5k_standard(self):
        """Female 5K open standard is 14:06 (846 seconds)."""
        standard = get_open_standard('5K', 'female')
        assert standard == 846

    def test_female_marathon_standard(self):
        """Female marathon open standard."""
        standard = get_open_standard('Marathon', 'female')
        assert standard == 7913

    # Gender handling
    def test_gender_case_insensitive(self):
        """Gender should be case-insensitive."""
        standard_lower = get_open_standard('5K', 'female')
        standard_upper = get_open_standard('5K', 'FEMALE')
        assert standard_lower == standard_upper

    def test_invalid_gender_defaults_to_male(self):
        """Invalid gender should default to male."""
        standard = get_open_standard('5K', 'invalid')
        assert standard == 755  # Male standard

    # Unknown distance
    def test_unknown_distance_returns_0(self):
        """Unknown distance should return 0."""
        standard = get_open_standard('100K', 'male')
        assert standard == 0


class TestCalculateAgeGrade:
    """Tests for calculate_age_grade function."""

    # Basic calculations
    def test_world_class_performance(self):
        """A time close to world record should give ~100% age grade."""
        # Male 5K in 12:40 (760 seconds) at age 30
        ag_pct, ag_time = calculate_age_grade(760, '5K', 30, 'male')
        assert ag_pct > 95  # Should be near 100%

    def test_typical_recreational_runner(self):
        """A typical recreational time should give ~50% age grade."""
        # Male 5K in 30:00 (1800 seconds) at age 35
        ag_pct, ag_time = calculate_age_grade(1800, '5K', 35, 'male')
        assert 35 < ag_pct < 50

    def test_v55_male_5k_example(self):
        """Test with known V55 male 5K time from module docstring."""
        # 18:16 = 1096 seconds
        ag_pct, ag_time = calculate_age_grade(1096, '5K', 55, 'male')
        # Should be around 81% based on the test in age_grading.py
        assert 80 < ag_pct < 82

    def test_v55_male_marathon_example(self):
        """Test with known V55 male marathon time."""
        # 2:55:42 = 10542 seconds
        ag_pct, ag_time = calculate_age_grade(10542, 'Marathon', 55, 'male')
        # Should be regional class level (a sub-3 marathon for a V55 is very good)
        assert 75 < ag_pct < 85

    # Age-graded time calculation
    def test_age_graded_time_younger_age(self):
        """Younger runners should have age-graded time close to actual."""
        ag_pct, ag_time = calculate_age_grade(1200, '5K', 30, 'male')
        # At age 30, factor is 1.0, so age-graded time = actual time
        assert ag_time == 1200

    def test_age_graded_time_older_age(self):
        """Older runners should have lower age-graded time."""
        ag_pct, ag_time = calculate_age_grade(1200, '5K', 55, 'male')
        # Factor is 0.8502, so age-graded time = 1200 * 0.8502 = 1020
        assert ag_time == int(1200 * 0.8502)

    # Edge cases
    def test_zero_time_returns_zero(self):
        """Zero time should return 0% age grade."""
        ag_pct, ag_time = calculate_age_grade(0, '5K', 30, 'male')
        assert ag_pct == 0.0
        assert ag_time == 0

    def test_unknown_distance_returns_zero(self):
        """Unknown distance should return 0% age grade."""
        ag_pct, ag_time = calculate_age_grade(1200, 'Unknown', 30, 'male')
        assert ag_pct == 0.0
        assert ag_time == 0

    # Gender comparison
    def test_same_time_different_gender(self):
        """Same time should give different age grades for different genders."""
        male_ag, _ = calculate_age_grade(1200, '5K', 30, 'male')
        female_ag, _ = calculate_age_grade(1200, '5K', 30, 'female')
        # Female standards are slower, so same time = higher age grade
        assert female_ag > male_ag

    # Result is properly rounded
    def test_result_is_rounded(self):
        """Age grade should be rounded to 1 decimal place."""
        ag_pct, _ = calculate_age_grade(1096, '5K', 55, 'male')
        # Check it's rounded (no more than 1 decimal)
        assert ag_pct == round(ag_pct, 1)


class TestGetAgeGradeCategory:
    """Tests for get_age_grade_category function."""

    def test_world_class_category(self):
        """90%+ should be World Class."""
        category, name = get_age_grade_category(95.0)
        assert category == 'world_class'
        assert name == 'World Class'

    def test_national_class_category(self):
        """80-89% should be National Class."""
        category, name = get_age_grade_category(85.0)
        assert category == 'national'
        assert name == 'National Class'

    def test_regional_class_category(self):
        """70-79% should be Regional Class."""
        category, name = get_age_grade_category(75.0)
        assert category == 'regional'
        assert name == 'Regional Class'

    def test_club_runner_category(self):
        """60-69% should be Club Runner."""
        category, name = get_age_grade_category(65.0)
        assert category == 'club'
        assert name == 'Club Runner'

    def test_recreational_category(self):
        """50-59% should be Recreational."""
        category, name = get_age_grade_category(55.0)
        assert category == 'recreational'
        assert name == 'Recreational'

    def test_beginner_category(self):
        """Below 50% should be Beginner."""
        category, name = get_age_grade_category(45.0)
        assert category == 'beginner'
        assert name == 'Beginner'

    # Boundary tests
    def test_boundary_90(self):
        """Exactly 90% should be World Class."""
        category, _ = get_age_grade_category(90.0)
        assert category == 'world_class'

    def test_boundary_80(self):
        """Exactly 80% should be National Class."""
        category, _ = get_age_grade_category(80.0)
        assert category == 'national'

    def test_boundary_70(self):
        """Exactly 70% should be Regional Class."""
        category, _ = get_age_grade_category(70.0)
        assert category == 'regional'

    def test_boundary_60(self):
        """Exactly 60% should be Club Runner."""
        category, _ = get_age_grade_category(60.0)
        assert category == 'club'

    def test_boundary_50(self):
        """Exactly 50% should be Recreational."""
        category, _ = get_age_grade_category(50.0)
        assert category == 'recreational'

    def test_boundary_just_below_50(self):
        """Just below 50% should be Beginner."""
        category, _ = get_age_grade_category(49.9)
        assert category == 'beginner'


class TestOpenStandardsData:
    """Tests to verify the open standards data is complete and valid."""

    def test_all_male_distances_present(self):
        """All expected distances should be present for males."""
        expected = ['5K', '10K', 'Half Marathon', 'Marathon', '10M']
        for distance in expected:
            assert distance in OPEN_STANDARDS['male']

    def test_all_female_distances_present(self):
        """All expected distances should be present for females."""
        expected = ['5K', '10K', 'Half Marathon', 'Marathon', '10M']
        for distance in expected:
            assert distance in OPEN_STANDARDS['female']

    def test_standards_are_positive(self):
        """All standards should be positive numbers."""
        for gender in OPEN_STANDARDS:
            for distance, time in OPEN_STANDARDS[gender].items():
                assert time > 0, f"{gender} {distance} standard should be positive"

    def test_female_standards_slower_than_male(self):
        """Female standards should be slower (larger) than male."""
        for distance in OPEN_STANDARDS['male']:
            if distance in OPEN_STANDARDS['female']:
                assert OPEN_STANDARDS['female'][distance] > OPEN_STANDARDS['male'][distance]


class TestWMAFactorsData:
    """Tests to verify the WMA factors data is complete and valid."""

    def test_age_range_30_to_100(self):
        """Factors should be available for ages 30-100."""
        for gender in ['male', 'female']:
            for distance in ['5K', '10K', 'Half Marathon', 'Marathon']:
                for age in range(30, 101):
                    assert age in WMA_FACTORS[gender][distance]

    def test_factors_between_0_and_1(self):
        """All factors should be between 0 and 1."""
        for gender in WMA_FACTORS:
            for distance in WMA_FACTORS[gender]:
                for age, factor in WMA_FACTORS[gender][distance].items():
                    assert 0 < factor <= 1.0, f"{gender} {distance} age {age} factor out of range"

    def test_factors_decrease_with_age(self):
        """Factors should generally decrease with age."""
        for gender in ['male', 'female']:
            for distance in ['5K', '10K', 'Half Marathon', 'Marathon']:
                # Check that 30 has higher factor than 100
                assert WMA_FACTORS[gender][distance][30] > WMA_FACTORS[gender][distance][100]

    def test_10m_factors_interpolated(self):
        """10M factors should be interpolated from 10K and Half Marathon."""
        for gender in ['male', 'female']:
            assert '10M' in WMA_FACTORS[gender]
            # Check a sample interpolation
            factor_10k = WMA_FACTORS[gender]['10K'][50]
            factor_hm = WMA_FACTORS[gender]['Half Marathon'][50]
            expected_10m = factor_10k * 0.4 + factor_hm * 0.6
            assert abs(WMA_FACTORS[gender]['10M'][50] - expected_10m) < 0.0001


class TestRealWorldExamples:
    """Tests using real-world running examples."""

    def test_elite_male_5k(self):
        """Elite male 5K time should give high age grade."""
        # 13:00 5K at age 25 (clamped to 30)
        ag_pct, _ = calculate_age_grade(780, '5K', 25, 'male')
        assert ag_pct > 90  # Should be world class

    def test_good_club_runner_10k(self):
        """Good club runner 10K time."""
        # 40:00 10K at age 40
        ag_pct, _ = calculate_age_grade(2400, '10K', 40, 'male')
        assert 60 < ag_pct < 75  # Club to regional level

    def test_average_marathon_time(self):
        """Average marathon finish time."""
        # 4:30:00 marathon at age 35
        ag_pct, _ = calculate_age_grade(16200, 'Marathon', 35, 'male')
        assert 40 < ag_pct < 55  # Recreational level

    def test_senior_runner_half_marathon(self):
        """Senior runner (V70) half marathon."""
        # 2:00:00 half marathon at age 70
        ag_pct, _ = calculate_age_grade(7200, 'Half Marathon', 70, 'male')
        # Should get significant age credit
        assert ag_pct > 55
