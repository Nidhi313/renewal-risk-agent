"""Agent wiring tests. A scripted fake chat model stands in for the LLM, so the
real LangGraph loop and real tools run without any API key or token spend."""
from datetime import date, timedelta

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

import src.agent as agent_mod
from src.tools import _contract, get_contract_terms, get_support_tickets, get_usage_data


class ScriptedModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


def _script(customer_id: str, final: str):
    calls = [
        {"name": t.name, "args": {"customer_id": customer_id}, "id": f"call_{i}"}
        for i, t in enumerate([get_usage_data, get_support_tickets, get_contract_terms])
    ]
    return ScriptedModel(messages=iter([AIMessage(content="", tool_calls=calls),
                                        AIMessage(content=final)]))


@pytest.fixture(autouse=True)
def _reset():
    agent_mod.build_agent.cache_clear()
    agent_mod._cache.clear()
    yield
    agent_mod.build_agent.cache_clear()
    agent_mod._cache.clear()


def test_agent_calls_all_three_tools_and_returns_verdict(monkeypatch):
    model = _script("cust_001", "Usage collapsed. Verdict: AT_RISK")
    monkeypatch.setattr(agent_mod, "build_model", lambda provider: model)
    graph = agent_mod.build_agent("groq")
    result = graph.invoke({"messages": [("user", "Assess renewal risk for customer_id: cust_001")]})
    tool_names = [m.name for m in result["messages"] if isinstance(m, ToolMessage)]
    assert sorted(tool_names) == ["get_contract_terms", "get_support_tickets", "get_usage_data"]
    assert agent_mod.extract_verdict(result["messages"][-1].content) == "AT_RISK"


def test_falls_back_when_primary_provider_fails(monkeypatch):
    monkeypatch.setattr(agent_mod.settings, "model_provider", "groq")
    monkeypatch.setattr(agent_mod.settings, "fallback_provider", "gemini")

    def fake_build(provider):
        if provider == "groq":
            raise RuntimeError("model decommissioned")
        return _script("cust_002", "Healthy. Verdict: NOT_AT_RISK")

    monkeypatch.setattr(agent_mod, "build_model", fake_build)
    result = agent_mod.assess("cust_002")
    assert result.provider == "gemini"
    assert result.verdict == "NOT_AT_RISK"


def test_second_call_is_served_from_cache(monkeypatch):
    calls = []

    def fake_build(provider):
        calls.append(provider)
        return _script("cust_003", "Verdict: AMBIGUOUS")

    monkeypatch.setattr(agent_mod, "build_model", fake_build)
    first = agent_mod.assess("cust_003")
    second = agent_mod.assess("cust_003")
    assert (first.cached, second.cached) == (False, True)
    assert len(calls) == 1


def test_all_providers_failing_raises(monkeypatch):
    def broken(provider):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(agent_mod, "build_model", broken)
    with pytest.raises(RuntimeError, match="All providers failed"):
        agent_mod.assess("cust_004")


@pytest.mark.parametrize("text,expected", [
    ("Final verdict: NOT_AT_RISK", "NOT_AT_RISK"),
    ("Not AT_RISK yet, but overall AMBIGUOUS", "AMBIGUOUS"),
    ("I considered NOT_AT_RISK. Verdict: AT_RISK", "AT_RISK"),
    ("no label here", None),
])
def test_extract_verdict(text, expected):
    assert agent_mod.extract_verdict(text) == expected


def test_renewal_dates_follow_the_calendar_not_import_time():
    later = date.today() + timedelta(days=30)
    assert _contract("cust_007", today=later)["renewal_date"] == later.isoformat()


def test_missing_usage_is_flagged_not_zero():
    out = get_usage_data.invoke({"customer_id": "cust_008"})
    assert out["data_available"] is False
    assert "usage_30d" not in out


def test_empty_ticket_history_is_still_a_populated_dict():
    out = get_support_tickets.invoke({"customer_id": "cust_001"})
    assert out == {"customer_id": "cust_001", "ticket_count": 0, "tickets": []}
