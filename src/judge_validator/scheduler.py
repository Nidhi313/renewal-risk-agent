"""Calibrate-then-sample scheduler: full validation runs per judge config
change or on a schedule, production traffic is spot-checked via sampling."""


def should_run_full_validation(judge_config_hash: str, last_validated_at) -> bool:
    raise NotImplementedError


def should_sample_this_request(sample_rate: float = 0.08) -> bool:
    raise NotImplementedError
