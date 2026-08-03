"""FastAPI entrypoint exposing the renewal-risk agent."""

from fastapi import FastAPI

app = FastAPI(title="Renewal Risk Agent")


@app.get("/health/")
def health():
    return {"status": "API is healthy and running!"}


@app.get("/predict/renewal-risk/")
def predict_renewal_risk(customer_id: str):
    raise NotImplementedError
