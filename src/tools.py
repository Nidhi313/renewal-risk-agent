from langchain_core.tools import tool

_FAKE_USAGE = {
    "cust_001": {"customer_id": "cust_001", "usage_30d": 12, "usage_90d_avg": 180, "trend": "declining"},
    "cust_002": {"customer_id": "cust_002", "usage_30d": 210, "usage_90d_avg": 190, "trend": "stable"},
    "cust_003": {"customer_id": "cust_003", "usage_30d": 95, "usage_90d_avg": 100, "trend": "flat"},
}

_FAKE_TICKETS = {
    "cust_001": [],  # no tickets -- usage dropped with no explanation, that's the red flag
    "cust_002": [{"id": "t1", "topic": "billing question", "sentiment": "neutral"}],
    "cust_003": [{"id": "t2", "topic": "feature request", "sentiment": "positive"},
                 {"id": "t3", "topic": "bug report", "sentiment": "frustrated"}],
}

_FAKE_CONTRACTS = {
    "cust_001": {"tier": "growth", "renewal_date": "2026-09-15", "annual_value": 24000},
    "cust_002": {"tier": "enterprise", "renewal_date": "2026-10-01", "annual_value": 96000},
    "cust_003": {"tier": "growth", "renewal_date": "2026-08-20", "annual_value": 30000},
}

@tool
def get_usage_data(customer_id: str) -> dict:
    """Return recent product usage metrics for a customer."""
    return _FAKE_USAGE.get(customer_id, {"customer_id": customer_id, "error": "not found"})

@tool
def get_support_tickets(customer_id: str) -> list[dict]:
    """Return recent support tickets for a customer."""
    return _FAKE_TICKETS.get(customer_id, [])

@tool
def get_contract_terms(customer_id: str) -> dict:
    """Return contract/renewal terms for a customer (renewal date, tier, value)."""
    return _FAKE_CONTRACTS.get(customer_id, {"customer_id": customer_id, "error": "not found"})