"""Repeated-trial consistency scorer (flip-rate) for the LLM judge.

Directly implements the metric from "The Coin Flip Judge?" (2026,
arxiv.org/pdf/2606.13685): run the identical judgment N times and measure
how often the verdict changes despite identical inputs. A judge that
flips its verdict on unchanged input is unreliable, even if any single
verdict looks confident.

Manually observed on this project already: a 30% flip rate across 3
repeated runs of the same 10-case suite (see notes doc / Excel tracker,
"Groq Repeated Trials" sheet). This module formalizes that manual finding
into a reusable check.
"""
from collections import Counter
from dataclasses import dataclass


@dataclass
class ConsistencyResult:
    case_id: str
    n_trials: int
    verdicts: list[str]
    majority_verdict: str
    flip_rate: float          # proportion of trials that disagreed with the majority
    is_consistent: bool       # flip_rate below the acceptability threshold


def compute_flip_rate(
    judge_fn,
    case,
    n_trials: int = 5,
    threshold: float = 0.2,
) -> ConsistencyResult:
    """Run the same judgment n_trials times on an unchanged case and
    measure how often the verdict disagrees with the majority.

    judge_fn: a callable that takes `case` and returns a verdict string
              (e.g. "AT_RISK" / "NOT_AT_RISK" / "AMBIGUOUS").
    case:     whatever judge_fn needs to produce one verdict -- kept
              generic so this works with the agent, the GEval judge, or
              any future judge, not just one specific model.
    threshold: flip rates at or above this are flagged inconsistent.
               0.2 is a deliberate starting point -- roughly matching the
               13.6% average from the paper with some margin, tightened
               later once more real data exists.
    """
    verdicts = [judge_fn(case) for _ in range(n_trials)]

    counts = Counter(verdicts)
    majority_verdict, majority_count = counts.most_common(1)[0]
    flip_rate = 1 - (majority_count / n_trials)

    return ConsistencyResult(
        case_id=getattr(case, "case_id", str(case)),
        n_trials=n_trials,
        verdicts=verdicts,
        majority_verdict=majority_verdict,
        flip_rate=flip_rate,
        is_consistent=flip_rate < threshold,
    )


def summarize_consistency(results: list[ConsistencyResult]) -> dict:
    """Aggregate flip-rate results across many cases into one report --
    this is the number that would actually go in a README or a
    calibration report: not "did it pass," but "how consistent is this
    judge, on average, across everything we tested."
    """
    if not results:
        return {"average_flip_rate": 0.0, "inconsistent_cases": [], "total_cases": 0}

    avg_flip_rate = sum(r.flip_rate for r in results) / len(results)
    inconsistent = [r.case_id for r in results if not r.is_consistent]

    return {
        "average_flip_rate": avg_flip_rate,
        "inconsistent_cases": inconsistent,
        "total_cases": len(results),
        "reference_point": (
            "The Coin Flip Judge? (2026) reported a mean flip rate of "
            "13.6% across 29 tasks -- arxiv.org/pdf/2606.13685"
        ),
    }