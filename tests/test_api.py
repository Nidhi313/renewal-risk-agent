"""HTTP-level tests. The agent is stubbed so these never call an LLM."""
from fastapi.testclient import TestClient

import src.main as main_mod
from src.agent import Assessment

client = TestClient(main_mod.app)


def test_health():
    assert client.get("/health/").json()["status"] == "ok"


def test_index_serves_ui():
    res = client.get("/")
    assert res.status_code == 200
    assert "Renewal Risk Agent" in res.text


def test_customers_lists_all_twenty_with_labels():
    rows = client.get("/customers/").json()
    assert len(rows) == 20
    assert all(r["expected_verdict"] in {"AT_RISK", "NOT_AT_RISK", "AMBIGUOUS"} for r in rows)


def test_unknown_customer_is_404_and_never_reaches_the_agent(monkeypatch):
    def boom(_):
        raise AssertionError("agent should not run")

    monkeypatch.setattr(main_mod, "assess", boom)
    assert client.get("/predict/renewal-risk/?customer_id=cust_999").status_code == 404


def test_predict_returns_verdict(monkeypatch):
    monkeypatch.setattr(main_mod, "assess", lambda cid: Assessment(
        cid, "Verdict: AT_RISK", "AT_RISK", "groq", "openai/gpt-oss-120b"))
    body = client.get("/predict/renewal-risk/?customer_id=cust_001").json()
    assert body["verdict"] == "AT_RISK" and body["provider"] == "groq"


def test_provider_outage_is_503(monkeypatch):
    def down(_):
        raise RuntimeError("All providers failed")

    monkeypatch.setattr(main_mod, "assess", down)
    assert client.get("/predict/renewal-risk/?customer_id=cust_001").status_code == 503
