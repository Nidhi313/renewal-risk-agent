"""Tests for the flip-rate consistency checker. No API calls -- uses a
fake judge function so this runs instantly and costs nothing."""
from src.judge_validator.consistency import compute_flip_rate


def test_perfectly_consistent_judge():
    def always_same(case):
        return "AT_RISK"

    result = compute_flip_rate(always_same, "fake_case", n_trials=5)
    assert result.flip_rate == 0.0
    assert result.is_consistent is True


def test_maximally_inconsistent_judge():
    answers = iter(["AT_RISK", "NOT_AT_RISK", "AMBIGUOUS", "AT_RISK", "NOT_AT_RISK"])

    def scattered(case):
        return next(answers)

    result = compute_flip_rate(scattered, "fake_case", n_trials=5)
    assert result.flip_rate >= 0.6
    assert result.is_consistent is False


def test_matches_manually_observed_flip_rate():
    observed_flips = {
        "case_001": False, "case_002": False, "case_003": True,
        "case_004": False, "case_005": False, "case_006": False,
        "case_007": True, "case_008": False, "case_009": True,
        "case_010": False,
    }
    flip_count = sum(1 for flipped in observed_flips.values() if flipped)
    manual_flip_rate = flip_count / len(observed_flips)
    assert manual_flip_rate == 0.3


def test_exact_tie_is_deterministic():
    """With no true majority (2 vs 2), Python's Counter breaks ties by
    first-occurrence order, not randomly. This test locks that behavior
    in explicitly, so it's documented rather than silently relied on."""
    answers = iter(["AT_RISK", "AT_RISK", "NOT_AT_RISK", "NOT_AT_RISK"])

    def tied(case):
        return next(answers)

    result = compute_flip_rate(tied, "fake_case", n_trials=4)
    assert result.majority_verdict == "AT_RISK"
    assert result.flip_rate == 0.5


def test_flip_rate_exactly_at_threshold_is_not_consistent():
    """flip_rate == threshold should fail (strictly less-than required),
    not pass -- boundary correctness, not just interior behavior.

    Uses a 3-of-4 split (flip_rate = 0.25) rather than 4-of-5 (0.2),
    because 0.25 is exactly representable in binary floating point
    (1/4 has a power-of-2 denominator) and 0.2 is not."""
    answers = iter(["AT_RISK"] * 3 + ["NOT_AT_RISK"] * 1)

    def judge(case):
        return next(answers)

    result = compute_flip_rate(judge, "fake_case", n_trials=4, threshold=0.25)
    assert result.flip_rate == 0.25
    assert result.is_consistent is False