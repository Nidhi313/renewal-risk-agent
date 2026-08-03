"""Tools available to the renewal-risk agent."""


def get_usage_data(customer_id: str) -> dict:
    """Return recent product usage metrics for a customer."""
    raise NotImplementedError


def get_support_tickets(customer_id: str) -> list[dict]:
    """Return recent support tickets for a customer."""
    raise NotImplementedError


def get_contract_terms(customer_id: str) -> dict:
    """Return contract/renewal terms for a customer (renewal date, tier, value)."""
    raise NotImplementedError
