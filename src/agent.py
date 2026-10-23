"""ReAct agent that assesses renewal risk for a customer account, built with LangGraph."""

import re
import time
from dataclasses import dataclass
from datetime import date
from functools import lru_cache

from langgraph.prebuilt import create_react_agent

from src.config import settings
from src.tools import get_contract_terms, get_support_tickets, get_usage_data

SYSTEM_PROMPT = """You are a renewal-risk analyst for a B2B SaaS company.
Given a customer_id, determine whether the account is at risk of churning
before renewal, and explain your reasoning citing the specific data you
looked at. Use the available tools to gather evidence before answering.
Do not guess at data you have not retrieved.

Always gather usage data, support ticket history, and contract terms
before reaching a conclusion, even if one signal alone seems decisive.

If usage data is unavailable, do not treat this as zero engagement --
flag it as a data quality gap and treat the case as ambiguous rather
than confidently at-risk.

When assessing risk, weigh usage and ticket signals together with how
much time remains until renewal. A concerning trend paired with a distant
renewal date suggests there is time to intervene and should generally be
treated as lower urgency than the same trend paired with an imminent
renewal. Do not treat a risk signal in isolation from the renewal
timeline -- the two must be reasoned about together.

Conclude every assessment with an explicit verdict, stated as exactly one
of: AT_RISK, NOT_AT_RISK, or AMBIGUOUS. Use AMBIGUOUS when signals
genuinely conflict or data is incomplete - this is a legitimate
conclusion, not a failure to decide, and should not be avoided in favor
of a false-confidence binary answer."""

TOOLS = [get_usage_data, get_support_tickets, get_contract_terms]
_VERDICT_RE = re.compile(r"\b(NOT_AT_RISK|AT_RISK|AMBIGUOUS)\b")


@dataclass
class Assessment:
    customer_id: str
    assessment: str
    verdict: str | None
    provider: str
    model: str
    cached: bool = False


def build_model(provider: str):
    """Chat model for a provider. Imports are local so a provider's package is
    only needed if that provider is actually used."""
    if provider == "groq":
        from langchain_groq import ChatGroq

        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not set")
        return ChatGroq(model=settings.groq_model, temperature=0, api_key=settings.groq_api_key,
                        max_retries=1)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        if not settings.google_api_key:
            raise RuntimeError("GOOGLE_API_KEY is not set")
        return ChatGoogleGenerativeAI(model=settings.gemini_model, temperature=0,
                                      google_api_key=settings.google_api_key, max_retries=1)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=settings.ollama_model, temperature=0)
    raise ValueError(f"Unknown provider: {provider!r}")


def model_name(provider: str) -> str:
    return {"groq": settings.groq_model, "gemini": settings.gemini_model,
            "ollama": settings.ollama_model}.get(provider, provider)


@lru_cache(maxsize=4)
def build_agent(provider: str | None = None):
    """Build once per provider and reuse; the compiled graph is stateless."""
    return create_react_agent(build_model(provider or settings.model_provider), TOOLS,
                              prompt=SYSTEM_PROMPT)


def extract_verdict(text: str) -> str | None:
    """The final verdict is the last of the three allowed labels in the text."""
    matches = _VERDICT_RE.findall(text or "")
    return matches[-1] if matches else None


def _final_text(result: dict) -> str:
    content = result["messages"][-1].content
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content


def run_agent(customer_id: str, provider: str | None = None, today: date | None = None) -> str:
    agent = build_agent(provider or settings.model_provider)
    today_s = (today or date.today()).isoformat()
    result = agent.invoke(
        {"messages": [("user", f"Today's date is {today_s}. "
                               f"Assess renewal risk for customer_id: {customer_id}")]}
    )
    return _final_text(result)


_cache: dict[tuple[str, str], tuple[float, Assessment]] = {}


def assess(customer_id: str, use_cache: bool = True) -> Assessment:
    """Run the agent with the primary provider, falling back to the secondary one
    if the primary errors (rate limit, retired model, missing key)."""
    key = (customer_id, date.today().isoformat())
    hit = _cache.get(key)
    if use_cache and hit and time.monotonic() - hit[0] < settings.cache_ttl_seconds:
        a = hit[1]
        return Assessment(**{**a.__dict__, "cached": True})

    providers = [settings.model_provider]
    if settings.fallback_provider and settings.fallback_provider != settings.model_provider:
        providers.append(settings.fallback_provider)

    errors = []
    for provider in providers:
        try:
            text = run_agent(customer_id, provider)
        except Exception as e:  # noqa: BLE001 -- any provider failure should trigger fallback
            errors.append(f"{provider}: {type(e).__name__}: {str(e)[:200]}")
            continue
        result = Assessment(customer_id, text, extract_verdict(text), provider, model_name(provider))
        _cache[key] = (time.monotonic(), result)
        return result
    raise RuntimeError("All providers failed. " + " | ".join(errors))


def assess_customer(customer_id: str) -> str:
    """Text-only interface kept for the eval harness."""
    return assess(customer_id, use_cache=False).assessment
