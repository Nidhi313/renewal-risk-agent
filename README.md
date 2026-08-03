# Renewal Risk Agent

An agent that assesses whether a B2B SaaS customer account is at risk of
churning before renewal, using usage data, support ticket history, and
contract terms. Built with LangGraph and served via FastAPI.

The project also includes a judge integrity toolkit that validates the
reliability of the LLM judge used to score the agent's outputs — checking
for position bias, run-to-run consistency, and calibration against
human-labeled cases — rather than assuming the judge's verdicts can be
trusted by default.

Deployed version: TBD

## Repository Structure

```
renewal-risk-agent/
├── src/
│   ├── main.py              <- FastAPI entrypoint
│   ├── config.py             <- Settings, loaded from environment
│   ├── agent.py              <- LangGraph ReAct agent
│   ├── tools.py               <- Tools available to the agent
│   ├── tracing.py             <- OpenTelemetry / Phoenix instrumentation
│   ├── eval/                  <- Golden-set evaluation (DeepEval / RAGAS)
│   └── judge_validator/       <- Judge reliability checks
├── data/golden_set/          <- Curated evaluation cases
├── tests/                     <- pytest suite
├── .github/workflows/         <- CI: runs tests + eval suite on push
├── Dockerfile
├── Makefile                   <- install / test / lint / run shortcuts
├── requirements.txt
├── pyproject.toml
└── .pre-commit-config.yaml   <- ruff, runs before each commit
```

## Approach

Most agent eval setups score an agent's output using an LLM judge and stop
there. This project adds a validation layer for the judge itself, based on
known reliability issues documented in recent LLM-as-judge research
(position bias, run-to-run inconsistency, and the gap between raw judge
agreement and calibrated agreement). See `data/golden_set/` for the
evaluation cases and `src/judge_validator/` for the checks.

Full write-up and research references: coming with the finished build.

## Installation

Clone the repository:

```
git clone https://github.com/Nidhi313/renewal-risk-agent.git
cd renewal-risk-agent
```

Install dependencies:

```
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your API keys, then run:

```
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## Status

Work in progress — agent, eval harness, and judge validator are being
built incrementally. See commit history for progress.
