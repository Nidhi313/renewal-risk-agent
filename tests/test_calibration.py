"""Tests for the calibration report. No API calls."""
from src.judge_validator.calibration import compute_calibration_report, interpret_kappa


def test_perfect_agreement():
    case_ids = ["c1", "c2", "c3"]
    human = ["PASS", "FAIL", "PASS"]
    judge = ["PASS", "FAIL", "PASS"]
    report = compute_calibration_report(case_ids, human, judge)
    assert report.raw_agreement == 1.0
    assert report.cohens_kappa == 1.0
    assert report.disagreements == []


def test_partial_agreement_flags_disagreements():
    case_ids = ["c1", "c2", "c3", "c4"]
    human = ["PASS", "FAIL", "PASS", "FAIL"]
    judge = ["PASS", "PASS", "PASS", "FAIL"]
    report = compute_calibration_report(case_ids, human, judge)
    assert report.raw_agreement == 0.75
    assert report.disagreements == [("c2", "FAIL", "PASS")]


def test_mismatched_lengths_raise():
    try:
        compute_calibration_report(["c1", "c2"], ["PASS"], ["PASS", "FAIL"])
        assert False, "should have raised"
    except ValueError:
        pass


def test_interpret_kappa_bands():
    assert interpret_kappa(0.9) == "almost perfect agreement"
    assert interpret_kappa(0.1) == "slight agreement"
    assert interpret_kappa(-0.1) == "worse than chance agreement"


def test_interpret_kappa_exact_boundaries():
    """Boundaries belong to the upper band (elif chains here use strict
    less-than), so e.g. exactly 0.20 is 'fair', not 'slight'. Locks in
    the actual behavior rather than leaving it ambiguous."""
    assert interpret_kappa(0.20) == "fair agreement"
    assert interpret_kappa(0.40) == "moderate agreement"
    assert interpret_kappa(0.60) == "substantial agreement"
    assert interpret_kappa(0.80) == "almost perfect agreement"


def test_single_case_kappa_does_not_crash():
    """n=1 makes kappa statistically undefined -- the implementation
    special-cases this to return 0.0 rather than erroring or calling
    sklearn with insufficient data. This test confirms it degrades
    gracefully instead of crashing on a tiny input."""
    report = compute_calibration_report(["c1"], ["PASS"], ["PASS"])
    assert report.cohens_kappa == 0.0
    assert report.n_cases == 1


def test_three_way_labels_matching_real_project_verdicts():
    """The actual label set this project uses is three-way
    (AT_RISK/NOT_AT_RISK/AMBIGUOUS), not the binary PASS/FAIL used in
    the tests above -- this exercises the real use case directly."""
    case_ids = [f"case_{i:03d}" for i in range(1, 10)]
    human  = ["AT_RISK", "NOT_AT_RISK", "AMBIGUOUS", "AT_RISK", "NOT_AT_RISK",
              "AMBIGUOUS", "AT_RISK", "NOT_AT_RISK", "AMBIGUOUS"]
    judge  = ["AT_RISK", "NOT_AT_RISK", "AT_RISK",   "AT_RISK", "NOT_AT_RISK",
              "AMBIGUOUS", "NOT_AT_RISK", "NOT_AT_RISK", "AMBIGUOUS"]

    report = compute_calibration_report(case_ids, human, judge)
    assert report.n_cases == 9
    assert len(report.disagreements) == 2  # case_003 and case_007 disagree
    assert report.raw_agreement == 7 / 9
    assert -1.0 <= report.cohens_kappa <= 1.0  # valid kappa range, sanity bound