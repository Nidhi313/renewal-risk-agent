"""FastAPI entrypoint exposing the renewal-risk agent."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agent import assess_customer
from src.config import settings
from src.tracing import init_tracing

app = FastAPI(title="Renewal Risk Agent")


@app.on_event("startup")
def _startup_tracing():
    """Start tracing once, when the API boots -- not per-request. If
    Phoenix isn't running locally, don't crash the whole API over it;
    tracing is observability, not a hard dependency for serving requests."""
    try:
        init_tracing()
    except Exception as e:
        print(f"Tracing did not start (continuing without it): {e}")


class RiskAssessmentResponse(BaseModel):
    customer_id: str
    assessment: str
    judge_provider: str


@app.get("/health/")
def health():
    return {"status": "API is healthy and running!"}


@app.get("/predict/renewal-risk/", response_model=RiskAssessmentResponse)
def predict_renewal_risk(customer_id: str):
    """Run the renewal-risk agent for a given customer_id and return its
    full reasoning + verdict. Each request triggers real LLM/tool calls
    -- treat this like a real cost, not a free lookup."""
    if not customer_id:
        raise HTTPException(status_code=400, detail="customer_id is required")

    try:
        assessment = assess_customer(customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return RiskAssessmentResponse(
        customer_id=customer_id,
        assessment=assessment,
        judge_provider=settings.model_provider,
    )