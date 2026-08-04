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
Do not guess at data you have not retrieved."""


def build_agent():
    """Construct the agent: the detective (model) + its assigned helpers (tools)."""
    model = ChatGoogleGenerativeAI(
                model="gemini-3.6-flash",
                google_api_key=settings.google_api_key,
                temperature=0,
            )
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