"""Calibrate-then-sample scheduler -- the cost-aware design piece.

Pattern: full validation (position_bias + consistency + calibration)
runs once per judge configuration, and again only on a schedule or when
the underlying model changes -- not on every request. Ongoing production
traffic gets spot-checked via random sampling, not exhaustively.

Without this module, the toolkit would multiply eval cost 3-5x forever
by re-validating on every single call -- exactly the naive design
rejected early in this project's planning (docs/PROJECT_DESIGN.md sec 4).
"""
import hashlib
import random
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class JudgeConfig:
    model_name: str
    prompt_version: str

    def fingerprint(self) -> str:
        """A short, stable hash representing 'which judge, exactly' --
        if either the model or the prompt changes, this changes, and
        that's the signal a re-validation is due."""
        raw = f"{self.model_name}::{self.prompt_version}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


def should_run_full_validation(
    config: JudgeConfig,
    last_validated: dict[str, datetime],
    revalidation_interval: timedelta = timedelta(days=7),
    now: datetime | None = None,
) -> bool:
    """Return True only if this exact judge config has never been
    validated, or its last validation is older than the interval.

    last_validated: a dict mapping fingerprint -> datetime of last full
                     validation. Caller owns persistence (this function
                     is pure, doesn't read/write any file or DB itself).
    now: injectable for testing -- avoids relying on the real clock.
    """
    now = now or datetime.now()
    fp = config.fingerprint()

    if fp not in last_validated:
        return True

    age = now - last_validated[fp]
    return age >= revalidation_interval


def should_sample_this_request(sample_rate: float = 0.08, rng: random.Random | None = None) -> bool:
    """Random sampling gate for production spot-checks.

    rng: injectable random source -- makes this testable/deterministic
         instead of relying on the global random module's hidden state.
    """
    if not 0.0 <= sample_rate <= 1.0:
        raise ValueError(f"sample_rate must be between 0 and 1, got {sample_rate}")
    rng = rng or random.Random()
    return rng.random() < sample_rate