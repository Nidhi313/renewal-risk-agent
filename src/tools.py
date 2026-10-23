"""Tools available to the renewal-risk agent, backed by a synthetic dataset.

Renewal dates are stored as offsets ("renewal_in_days") and turned into real
dates at call time. Computing them once at import time meant a long-running
server slowly drifted out of sync with the date the agent is told is "today".
"""
from datetime import date, timedelta

from langchain_core.tools import tool

_FAKE_USAGE = {
    "cust_001": {"customer_id": "cust_001", "usage_30d": 12, "usage_90d_avg": 180, "trend": "declining"},
    "cust_002": {"customer_id": "cust_002", "usage_30d": 210, "usage_90d_avg": 190, "trend": "stable"},
    "cust_003": {"customer_id": "cust_003", "usage_30d": 95, "usage_90d_avg": 100, "trend": "flat"},
    "cust_004": {"customer_id": "cust_004", "usage_30d": 8, "usage_90d_avg": 150, "trend": "declining"},
    "cust_005": {"customer_id": "cust_005", "usage_30d": 175, "usage_90d_avg": 180, "trend": "stable"},
    "cust_006": {"customer_id": "cust_006", "usage_30d": 340, "usage_90d_avg": 200, "trend": "rising"},
    "cust_007": {"customer_id": "cust_007", "usage_30d": 150, "usage_90d_avg": 155, "trend": "stable"},
    "cust_008": {"customer_id": "cust_008", "usage_30d": None, "usage_90d_avg": None, "trend": "unknown"},
    "cust_009": {"customer_id": "cust_009", "usage_30d": 110, "usage_90d_avg": 150, "trend": "declining"},
    "cust_010": {"customer_id": "cust_010", "usage_30d": 98, "usage_90d_avg": 100, "trend": "flat"},
}

_FAKE_TICKETS = {
    "cust_001": [],
    "cust_002": [{"id": "t1", "topic": "billing question", "sentiment": "neutral"}],
    "cust_003": [
        {"id": "t2", "topic": "feature request", "sentiment": "positive"},
        {"id": "t3", "topic": "bug report", "sentiment": "frustrated"},
    ],
    "cust_004": [],
    "cust_005": [
        {"id": "t4", "topic": "outage complaint", "sentiment": "angry", "status": "unresolved"},
        {"id": "t5", "topic": "billing dispute", "sentiment": "angry", "status": "unresolved"},
        {"id": "t6", "topic": "missed SLA", "sentiment": "angry", "status": "unresolved"},
    ],
    "cust_006": [{"id": "t7", "topic": "expansion inquiry", "sentiment": "positive"}],
    "cust_007": [{"id": "t8", "topic": "general question", "sentiment": "neutral"}],
    "cust_008": [],
    "cust_009": [
        {"id": "t9", "topic": "feature request", "sentiment": "positive"},
        {"id": "t10", "topic": "onboarding question", "sentiment": "neutral"},
    ],
    "cust_010": [],
}

_FAKE_CONTRACTS = {  # renewal is expressed as days from "today" so the scenarios never go stale
    "cust_001": {"tier": "growth", "renewal_in_days": 41, "annual_value": 24000},
    "cust_002": {"tier": "enterprise", "renewal_in_days": 57, "annual_value": 96000},
    "cust_003": {"tier": "growth", "renewal_in_days": 15, "annual_value": 30000},
    "cust_004": {"tier": "growth", "renewal_in_days": 199, "annual_value": 28000},
    "cust_005": {"tier": "enterprise", "renewal_in_days": 10, "annual_value": 120000},
    "cust_006": {"tier": "growth", "renewal_in_days": 30, "annual_value": 32000},
    "cust_007": {"tier": "growth", "renewal_in_days": 0, "annual_value": 27000},
    "cust_008": {"tier": "growth", "renewal_in_days": 20, "annual_value": 25000},
    "cust_009": {"tier": "enterprise", "renewal_in_days": 60, "annual_value": 88000},
    "cust_010": {"tier": "growth", "renewal_in_days": 5, "annual_value": 26000},
}

_FAKE_USAGE.update({
    "cust_011": {"customer_id": "cust_011", "usage_30d": 5, "usage_90d_avg": 200, "trend": "declining"},
    "cust_012": {"customer_id": "cust_012", "usage_30d": 500, "usage_90d_avg": 210, "trend": "rising"},
    "cust_013": {"customer_id": "cust_013", "usage_30d": 80, "usage_90d_avg": 160, "trend": "declining"},
    "cust_014": {"customer_id": "cust_014", "usage_30d": 300, "usage_90d_avg": 280, "trend": "rising"},
    "cust_015": {"customer_id": "cust_015", "usage_30d": 100, "usage_90d_avg": 102, "trend": "flat"},
    "cust_016": {"customer_id": "cust_016", "usage_30d": None, "usage_90d_avg": None, "trend": "unknown"},
    "cust_017": {"customer_id": "cust_017", "usage_30d": 90, "usage_90d_avg": 140, "trend": "declining"},
    "cust_018": {"customer_id": "cust_018", "usage_30d": 50, "usage_90d_avg": 55, "trend": "flat"},
    "cust_019": {"customer_id": "cust_019", "usage_30d": 15, "usage_90d_avg": 180, "trend": "declining"},
    "cust_020": {"customer_id": "cust_020", "usage_30d": 120, "usage_90d_avg": 118, "trend": "stable"},
})

_FAKE_TICKETS.update({
    "cust_011": [],
    "cust_012": [{"id": "t11", "topic": "expansion inquiry", "sentiment": "positive"}],
    "cust_013": [
        {"id": "t12", "topic": "feature praise", "sentiment": "positive"},
        {"id": "t13", "topic": "feature praise 2", "sentiment": "positive"},
    ],
    "cust_014": [{"id": "t14", "topic": "critical outage", "sentiment": "very_negative", "status": "unresolved"}],
    "cust_015": [],
    "cust_016": [],
    "cust_017": [
        {"id": "t15", "topic": "pricing complaint", "sentiment": "negative", "status": "unresolved"},
        {"id": "t16", "topic": "feature request", "sentiment": "positive"},
    ],
    "cust_018": [{"id": "t17", "topic": "billing question", "sentiment": "neutral"}],
    "cust_019": [],
    "cust_020": [],
})

_FAKE_CONTRACTS.update({
    "cust_011": {"tier": "growth", "renewal_in_days": 3, "annual_value": 22000},
    "cust_012": {"tier": "enterprise", "renewal_in_days": 4, "annual_value": 150000},
    "cust_013": {"tier": "growth", "renewal_in_days": 45, "annual_value": 29000},
    "cust_014": {"tier": "enterprise", "renewal_in_days": 12, "annual_value": 110000},
    "cust_015": {"tier": "growth", "renewal_in_days": 150, "annual_value": 21000},
    "cust_016": {"tier": "growth", "renewal_in_days": 10, "annual_value": 24000},
    "cust_017": {"tier": "growth", "renewal_in_days": 18, "annual_value": 27000},
    "cust_018": {"tier": "enterprise", "renewal_in_days": 90, "annual_value": 200000},
    "cust_019": {"tier": "growth", "renewal_in_days": 250, "annual_value": 18000},
    "cust_020": {"tier": "growth", "renewal_in_days": 0, "annual_value": 24000},
})


def known_customer_ids() -> list[str]:
    return sorted(_FAKE_CONTRACTS)


def is_known_customer(customer_id: str) -> bool:
    return customer_id in _FAKE_CONTRACTS


def _usage(customer_id: str) -> dict:
    data = _FAKE_USAGE.get(customer_id)
    if data is None:
        return {"customer_id": customer_id, "error": "not found"}
    if data.get("usage_30d") is None:
        return {
            "customer_id": customer_id,
            "data_available": False,
            "note": "Usage data is missing/not synced for this customer. Do not interpret as zero usage.",
        }
    return {**data, "data_available": True}


def _tickets(customer_id: str) -> dict:
    # Always a populated dict, never a bare empty list: Groq rejects empty-list tool results.
    tickets = _FAKE_TICKETS.get(customer_id, [])
    return {"customer_id": customer_id, "ticket_count": len(tickets), "tickets": tickets}


def _contract(customer_id: str, today: date | None = None) -> dict:
    # Same fields the agent always saw (tier, renewal_date, annual_value). Days-until-renewal
    # is deliberately NOT given to the agent: working it out from the date is part of what
    # the golden set tests, so adding it here would change the experiment.
    terms = _FAKE_CONTRACTS.get(customer_id)
    if terms is None:
        return {"customer_id": customer_id, "error": "not found"}
    today = today or date.today()
    return {
        "tier": terms["tier"],
        "renewal_date": (today + timedelta(days=terms["renewal_in_days"])).isoformat(),
        "annual_value": terms["annual_value"],
    }


def customer_snapshot(customer_id: str) -> dict:
    """Raw signals for one customer, no LLM involved. Used by the UI."""
    return {
        "usage": _usage(customer_id),
        "tickets": _tickets(customer_id),
        "contract": {
            **_contract(customer_id),
            "days_until_renewal": _FAKE_CONTRACTS[customer_id]["renewal_in_days"],
        },
    }


@tool
def get_usage_data(customer_id: str) -> dict:
    """Return recent product usage metrics for a customer."""
    return _usage(customer_id)


@tool
def get_support_tickets(customer_id: str) -> dict:
    """Return recent support tickets for a customer."""
    return _tickets(customer_id)


@tool
def get_contract_terms(customer_id: str) -> dict:
    """Return contract/renewal terms for a customer (renewal date, tier, value)."""
    return _contract(customer_id)
