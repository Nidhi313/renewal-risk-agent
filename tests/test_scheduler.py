"""Tests for the calibrate-then-sample scheduler. No API calls, no real
clock or randomness -- both time and randomness are injected."""
import random
from datetime import datetime, timedelta

from src.judge_validator.scheduler import (
    JudgeConfig,
    should_run_full_validation,
    should_sample_this_request,
)


def test_fingerprint_changes_with_model_or_prompt():
    a = JudgeConfig(model_name="llama-3.3-70b-versatile", prompt_version="v1")
    b = JudgeConfig(model_name="llama-3.3-70b-versatile", prompt_version="v2")
    c = JudgeConfig(model_name="gemini-3.6-flash", prompt_version="v1")
    assert a.fingerprint() != b.fingerprint()  # prompt changed
    assert a.fingerprint() != c.fingerprint()  # model changed
    assert a.fingerprint() == JudgeConfig(model_name="llama-3.3-70b-versatile", prompt_version="v1").fingerprint()


def test_first_time_config_always_validates():
    config = JudgeConfig(model_name="new-model", prompt_version="v1")
    result = should_run_full_validation(config, last_validated={})
    assert result is True


def test_recently_validated_config_skips():
    config = JudgeConfig(model_name="m", prompt_version="v1")
    now = datetime(2026, 8, 10)
    last_validated = {config.fingerprint(): now - timedelta(days=1)}
    result = should_run_full_validation(config, last_validated, revalidation_interval=timedelta(days=7), now=now)
    assert result is False


def test_stale_validation_triggers_revalidation():
    config = JudgeConfig(model_name="m", prompt_version="v1")
    now = datetime(2026, 8, 10)
    last_validated = {config.fingerprint(): now - timedelta(days=8)}
    result = should_run_full_validation(config, last_validated, revalidation_interval=timedelta(days=7), now=now)
    assert result is True


def test_exactly_at_interval_boundary_triggers():
    """age >= interval, not >, so exactly 7 days should count as due."""
    config = JudgeConfig(model_name="m", prompt_version="v1")
    now = datetime(2026, 8, 10)
    last_validated = {config.fingerprint(): now - timedelta(days=7)}
    result = should_run_full_validation(config, last_validated, revalidation_interval=timedelta(days=7), now=now)
    assert result is True


def test_sample_rate_zero_never_samples():
    rng = random.Random(42)
    results = [should_sample_this_request(sample_rate=0.0, rng=rng) for _ in range(100)]
    assert all(r is False for r in results)


def test_sample_rate_one_always_samples():
    rng = random.Random(42)
    results = [should_sample_this_request(sample_rate=1.0, rng=rng) for _ in range(100)]
    assert all(r is True for r in results)


def test_sample_rate_roughly_matches_over_many_trials():
    """Deterministic seed -- checks the sample rate lands in a sane
    range over many trials, not an exact count (which would be flaky)."""
    rng = random.Random(7)
    results = [should_sample_this_request(sample_rate=0.08, rng=rng) for _ in range(1000)]
    observed_rate = sum(results) / 1000
    assert 0.04 < observed_rate < 0.14  # generous band around 0.08


def test_invalid_sample_rate_raises():
    try:
        should_sample_this_request(sample_rate=1.5)
        assert False, "should have raised"
    except ValueError:
        pass