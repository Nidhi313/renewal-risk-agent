"""FastAPI entrypoint exposing the renewal-risk agent and a small demo UI."""

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.agent import assess
from src.config import settings
from src.tools import customer_snapshot, is_known_customer, known_customer_ids

STATIC_DIR = Path(__file__).parent / "static"
GOLDEN_SET_PATH = Path(__file__).parent.parent / "data" / "golden_set" / "cases.jsonl"


def _load_golden_set() -> dict[str, dict]:
    if not GOLDEN_SET_PATH.exists():
        return {}
    cases = (json.loads(line) for line in GOLDEN_SET_PATH.read_text().splitlines() if line.strip())
    return {c["customer_id"]: c for c in cases}


GOLDEN = _load_golden_set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tracing is opt-in. Phoenix is a dev dependency, and launching its UI inside
    # a 512 MB hosting container costs memory for a dashboard nobody can reach.
    if settings.enable_tracing:
        try:
            from src.tracing import init_tracing

            init_tracing()
        except Exception as e:  # noqa: BLE001
            print(f"Tracing did not start (continuing without it): {e}")
    yield


app = FastAPI(title="Renewal Risk Agent", lifespan=lifespan)


class RiskAssessmentResponse(BaseModel):
    customer_id: str
    verdict: str | None
    assessment: str
    provider: str
    model: str
    cached: bool


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health/")
def health():
    return {"status": "ok", "provider": settings.model_provider,
            "fallback_provider": settings.fallback_provider or None}


@app.get("/customers/")
def customers():
    """Raw signals for every synthetic customer plus its golden-set label. No LLM calls."""
    out = []
    for cid in known_customer_ids():
        case = GOLDEN.get(cid, {})
        out.append({
            "customer_id": cid,
            **customer_snapshot(cid),
            "scenario": case.get("scenario_description"),
            "expected_verdict": (case.get("expected_verdict") or "").upper() or None,
            "is_edge_case": case.get("is_edge_case", False),
        })
    return out


@app.get("/predict/renewal-risk/", response_model=RiskAssessmentResponse)
def predict_renewal_risk(customer_id: str):
    """Run the agent for one customer. Each uncached call makes real LLM and tool
    calls, so unknown IDs are rejected before any model is touched."""
    if not is_known_customer(customer_id):
        raise HTTPException(status_code=404, detail=f"Unknown customer_id: {customer_id}")
    try:
        result = assess(customer_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Agent unavailable: {e}") from e
    return RiskAssessmentResponse(**result.__dict__)
