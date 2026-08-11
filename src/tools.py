"""Tools available to the renewal-risk agent."""
from langchain_core.tools import tool
from datetime import date, timedelta

_TODAY = date.today()

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

_FAKE_CONTRACTS = {
    "cust_001": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=41)).isoformat(), "annual_value": 24000},
    "cust_002": {"tier": "enterprise", "renewal_date": (_TODAY + timedelta(days=57)).isoformat(), "annual_value": 96000},
    "cust_003": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=15)).isoformat(), "annual_value": 30000},
    "cust_004": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=199)).isoformat(), "annual_value": 28000},
    "cust_005": {"tier": "enterprise", "renewal_date": (_TODAY + timedelta(days=10)).isoformat(), "annual_value": 120000},
    "cust_006": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=30)).isoformat(), "annual_value": 32000},
    "cust_007": {"tier": "growth", "renewal_date": _TODAY.isoformat(), "annual_value": 27000},
    "cust_008": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=20)).isoformat(), "annual_value": 25000},
    "cust_009": {"tier": "enterprise", "renewal_date": (_TODAY + timedelta(days=60)).isoformat(), "annual_value": 88000},
    "cust_010": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=5)).isoformat(), "annual_value": 26000},
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
    "cust_011": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=3)).isoformat(), "annual_value": 22000},
    "cust_012": {"tier": "enterprise", "renewal_date": (_TODAY + timedelta(days=4)).isoformat(), "annual_value": 150000},
    "cust_013": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=45)).isoformat(), "annual_value": 29000},
    "cust_014": {"tier": "enterprise", "renewal_date": (_TODAY + timedelta(days=12)).isoformat(), "annual_value": 110000},
    "cust_015": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=150)).isoformat(), "annual_value": 21000},
    "cust_016": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=10)).isoformat(), "annual_value": 24000},
    "cust_017": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=18)).isoformat(), "annual_value": 27000},
    "cust_018": {"tier": "enterprise", "renewal_date": (_TODAY + timedelta(days=90)).isoformat(), "annual_value": 200000},
    "cust_019": {"tier": "growth", "renewal_date": (_TODAY + timedelta(days=250)).isoformat(), "annual_value": 18000},
    "cust_020": {"tier": "growth", "renewal_date": _TODAY.isoformat(), "annual_value": 24000},
})

@tool
def get_usage_data(customer_id: str) -> dict:
    """Return recent product usage metrics for a customer."""
    data = _FAKE_USAGE.get(customer_id, {"customer_id": customer_id, "error": "not found"})
    if data.get("usage_30d") is None:
        return {
            "customer_id": customer_id,
            "data_available": False,
            "note": "Usage data is missing/not synced for this customer. Do not interpret as zero usage.",
        }
    return {**data, "data_available": True}


@tool
def get_support_tickets(customer_id: str) -> dict:
    """Return recent support tickets for a customer."""
    tickets = _FAKE_TICKETS.get(customer_id, [])
    return {"customer_id": customer_id, "ticket_count": len(tickets), "tickets": tickets}


@tool
def get_contract_terms(customer_id: str) -> dict:
    """Return contract/renewal terms for a customer (renewal date, tier, value)."""
    return _FAKE_CONTRACTS.get(customer_id, {"customer_id": customer_id, "error": "not found"})
