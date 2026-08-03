"""Schema for the golden evaluation dataset."""
from dataclasses import dataclass


@dataclass
class GoldenCase:
    case_id: str
    customer_id: str
    scenario_description: str
    expected_verdict: str               # "at_risk" | "not_at_risk" | "ambiguous"
    expected_reasoning_keywords: list[str]
    is_edge_case: bool = False
