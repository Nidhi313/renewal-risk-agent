"""ReAct agent that assesses renewal risk for a customer account, built with LangGraph."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from src.tools import get_usage_data, get_support_tickets, get_contract_terms
from src.config import settings
from datetime import date

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

def build_agent():
    if settings.model_provider == "ollama":
        from langchain_ollama import ChatOllama
        model = ChatOllama(model="llama3.2", temperature=0)
    elif settings.model_provider == "groq":
        from langchain_groq import ChatGroq
        model = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=settings.groq_api_key)
    else:
        model = ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.google_api_key, temperature=0)
    tools = [get_usage_data, get_support_tickets, get_contract_terms]
    return create_react_agent(model, tools, prompt=SYSTEM_PROMPT)


def assess_customer(customer_id: str) -> str:
    """Hand the detective a case and get back the final verdict."""
    agent = build_agent()
    today = date.today().isoformat()
    result = agent.invoke(
        {"messages": [("user", f"Today's date is {today}. Assess renewal risk for customer_id: {customer_id}")]}
    )
    content = result["messages"][-1].content
    if isinstance(content, list):
        return "".join(block.get("text", "") for block in content if isinstance(block, dict))
    return content