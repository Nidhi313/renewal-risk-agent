"""Tests for the position-swap bias checker. No API calls."""
import pytest
from src.judge_validator.position_bias import check_position_bias, check_position_bias_batch


def test_unbiased_judge_shows_no_bias():
    def judge_longer_string(first, second):
        return "A" if len(first) >= len(second) else "B"

    result = check_position_bias(judge_longer_string, "short", "much longer string")
    assert result.bias_detected is False
    assert result.preferred_when_normal_order == "much longer string"
    assert result.preferred_when_swapped_order == "much longer string"


def test_biased_judge_always_prefers_first_position():
    def always_prefers_first(first, second):
        return "A"

    result = check_position_bias(always_prefers_first, "item_1", "item_2")
    assert result.bias_detected is True
    assert result.preferred_when_normal_order == "item_1"
    assert result.preferred_when_swapped_order == "item_2"


def test_biased_judge_always_prefers_second_position():
    """Mirror of the first-position test -- bias can favor whichever
    slot, not just slot A. Both directions need coverage."""
    def always_prefers_second(first, second):
        return "B"

    result = check_position_bias(always_prefers_second, "item_1", "item_2")
    assert result.bias_detected is True
    assert result.preferred_when_normal_order == "item_2"
    assert result.preferred_when_swapped_order == "item_1"


def test_batch_bias_rate_computation():
    def always_prefers_first(first, second):
        return "A"

    pairs = [("a1", "a2"), ("b1", "b2"), ("c1", "c2")]
    summary = check_position_bias_batch(always_prefers_first, pairs)
    assert summary["total_pairs"] == 3
    assert summary["biased_count"] == 3
    assert summary["bias_rate"] == 1.0


def test_malformed_judge_output_raises():
    """A judge returning anything other than 'A'/'B' should fail loudly,
    not be silently misinterpreted as a real preference."""
    def broken_judge(first, second):
        return "TIE"

    with pytest.raises(ValueError):
        check_position_bias(broken_judge, "item_1", "item_2")