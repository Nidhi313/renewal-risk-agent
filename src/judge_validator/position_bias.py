"""Position-swap bias checker for the LLM judge.

Checks whether a judge's preference between two items changes purely
because of the order they were shown in -- a known, named failure mode
in the 2026 judge-reliability literature (see docs/PROJECT_DESIGN.md
references, e.g. arxiv.org/pdf/2603.01865 and arxiv.org/pdf/2606.13685).

Different from consistency.py: that module asks "does the judge agree
with itself on an unchanged input, repeated." This module asks "does the
judge's answer change just because of *order*, on the same underlying
comparison." Both are real, separate reliability failures.

Useful directly on this project: comparing two versions of an agent's
output (e.g. before/after a system prompt change, like the joint-
reasoning fix earlier) is exactly a pairwise comparison task -- this
module can check whether "which version is better" judgments are
actually trustworthy, or just reflect whichever was shown first.
"""
from dataclasses import dataclass


@dataclass
class PositionBiasResult:
    preferred_when_normal_order: str
    preferred_when_swapped_order: str
    bias_detected: bool
    verdict_normal: str
    verdict_swapped: str


def check_position_bias(judge_fn, item_a, item_b) -> PositionBiasResult:
    """Run the same comparison twice, with item order swapped, and check
    whether the judge's real preference stayed consistent.

    judge_fn: a callable taking (first_item, second_item) and returning
              "A" or "B". Any other return value is treated as a
              malformed judge response and raises ValueError -- silently
              guessing what an unexpected output "meant" would defeat
              the point of a reliability checker.
    """
    verdict_normal = judge_fn(item_a, item_b)
    verdict_swapped = judge_fn(item_b, item_a)

    for verdict in (verdict_normal, verdict_swapped):
        if verdict not in ("A", "B"):
            raise ValueError(
                f"judge_fn returned {verdict!r}, expected 'A' or 'B'. "
                "A position-bias check cannot interpret an unexpected verdict."
            )

    preferred_normal = item_a if verdict_normal == "A" else item_b
    preferred_swapped = item_b if verdict_swapped == "A" else item_a

    return PositionBiasResult(
        preferred_when_normal_order=preferred_normal,
        preferred_when_swapped_order=preferred_swapped,
        bias_detected=preferred_normal != preferred_swapped,
        verdict_normal=verdict_normal,
        verdict_swapped=verdict_swapped,
    )


def check_position_bias_batch(judge_fn, pairs: list[tuple]) -> dict:
    results = [check_position_bias(judge_fn, a, b) for a, b in pairs]
    biased_count = sum(1 for r in results if r.bias_detected)
    return {
        "total_pairs": len(results),
        "biased_count": biased_count,
        "bias_rate": biased_count / len(results) if results else 0.0,
        "results": results,
    }