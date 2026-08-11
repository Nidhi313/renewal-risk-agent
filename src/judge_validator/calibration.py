"""Human-labeled calibration report for the LLM judge.

Per docs/PROJECT_DESIGN.md section 3, citing arxiv.org/abs/2606.19544
("Reliability without Validity"): raw agreement between a judge and a
human overstates the judge's real discriminative ability, because a
judge that just guesses the majority class can score high agreement
without actually being useful. Cohen's kappa corrects for exactly this
by accounting for how much agreement would be expected by chance alone.

This module is intentionally simple -- it doesn't call any model itself.
It takes two label lists (your own human judgments, and the judge's
verdicts on the same cases) and reports the honest comparison. The human
labeling step has to happen outside this code, by you, looking at real
outputs.
"""
from dataclasses import dataclass

from sklearn.metrics import cohen_kappa_score


@dataclass
class CalibrationReport:
    n_cases: int
    raw_agreement: float
    cohens_kappa: float
    disagreements: list[tuple]   # (case_id, human_label, judge_label) where they differed


def compute_calibration_report(
    case_ids: list[str],
    human_labels: list[str],
    judge_labels: list[str],
) -> CalibrationReport:
    """Compare human judgment against judge verdicts on the same cases.

    All three lists must be the same length and in the same case order.
    Labels should use a small, consistent vocabulary (e.g. "PASS"/"FAIL"
    or "AT_RISK"/"NOT_AT_RISK"/"AMBIGUOUS") -- free text won't work here.
    """
    if not (len(case_ids) == len(human_labels) == len(judge_labels)):
        raise ValueError("case_ids, human_labels, and judge_labels must be the same length")

    n = len(case_ids)
    agreements = sum(1 for h, j in zip(human_labels, judge_labels) if h == j)
    raw_agreement = agreements / n if n else 0.0

    kappa = cohen_kappa_score(human_labels, judge_labels) if n > 1 else 0.0

    disagreements = [
        (cid, h, j)
        for cid, h, j in zip(case_ids, human_labels, judge_labels)
        if h != j
    ]

    return CalibrationReport(
        n_cases=n,
        raw_agreement=raw_agreement,
        cohens_kappa=kappa,
        disagreements=disagreements,
    )


def interpret_kappa(kappa: float) -> str:
    """Standard Landis & Koch interpretation bands -- gives the number
    context instead of leaving it to be misread as a percentage."""
    if kappa < 0:
        return "worse than chance agreement"
    elif kappa < 0.20:
        return "slight agreement"
    elif kappa < 0.40:
        return "fair agreement"
    elif kappa < 0.60:
        return "moderate agreement"
    elif kappa < 0.80:
        return "substantial agreement"
    else:
        return "almost perfect agreement"