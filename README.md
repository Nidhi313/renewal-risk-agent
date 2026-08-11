# Renewal Risk Agent

An agent that assesses whether a B2B SaaS customer account is at risk of
churning before renewal, using usage data, support ticket history, and
contract terms. Built with LangGraph and served via FastAPI.

The project also includes a judge integrity toolkit that validates the
reliability of the LLM judge used to score the agent's outputs — checking
for position bias, run-to-run consistency, and calibration against
human-labeled cases — rather than assuming the judge's verdicts can be
trusted by default.

Deployed version: [https://renewal-risk-agent.onrender.com](https://renewal-risk-agent.onrender.com)

Example: `GET /predict/renewal-risk/?customer_id=cust_001` (also try cust_002 through cust_020 — see `data/golden_set/cases.jsonl` for the full scenario list)

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
evaluation cases, `src/judge_validator/` for the checks, and the
Findings section below for what this actually surfaced.

## Findings

**Two real bugs found and fixed during development:**
1. An empty ticket list caused a 400 error on Groq specifically (its
   message validator rejects empty-list tool responses; Gemini had been
   silently tolerating this). Fixed by having the tool always return a
   populated dict, even when the ticket count is zero.
2. The agent was treating missing usage data (`None`) as zero engagement
   instead of a data quality gap. Fixed at the tool level (an explicit
   `data_available` flag) and reinforced in the system prompt.

**Judge reliability findings, using the Judge Integrity Toolkit built in
this project:**
- **Flip rate:** running the identical 10-case suite 3 times with zero
  code changes produced a 30% verdict flip rate on 3 of 10 cases —
  close to the 13.6% average reported in "The Coin Flip Judge?" (2026),
  actually higher on this smaller sample.
- **Human calibration:** independent human labeling against the actual
  judge produced 80% raw agreement but a Cohen's kappa of only 0.375
  ("fair" agreement) — a live demonstration of the exact problem
  "Reliability without Validity" (2026) documents: raw agreement
  overstates a judge's real discriminative ability.
- **Ambiguity detection gap, quantified across 20 cases:** cases
  designed to have genuinely conflicting signals (warranting an
  AMBIGUOUS verdict) passed at 55% (6/11), versus 89% (8/9) for
  clear-cut cases — a real, 34-point gap, not an isolated failure.
- **Cross-model judge comparison:** re-scoring the same agent outputs
  with a second, independent judge (Gemini) showed Groq landing on the
  minority side of a 2-vs-1 disagreement — once against a human, once
  against Gemini — on both contested cases. Real evidence that judge
  choice measurably affects reliability, not just cost or speed.

**Deliberate non-fixes:** several findings above were not "fixed" by
further prompt engineering, on purpose. Chasing individual case failures
with more prompt instructions risks overfitting the prompt to this
specific golden set rather than improving general reasoning. The two
system prompt changes that were made (joint usage/timeline reasoning,
standardized verdict vocabulary) were kept general on purpose, tested
for whether they generalized to cases they weren't written for, and
adopted only after that check passed.

## Known Limitations & Future Coverage

This golden set is deliberately structured, not exhaustive. It covers
the three core decision axes the agent reasons over (usage trend, ticket
sentiment, renewal timing) including their conflicting combinations, but
does not claim to represent every scenario a production system would
face. Real gaps not yet covered: seasonality-driven usage dips, champion
departure / stakeholder change, explicitly stated churn intent,
multi-product usage patterns, billing/payment history, and
customer-specific history (has this account dipped and recovered
before).

**Open hypothesis, weaker evidence:** cases where the renewal date falls
exactly on the current day failed in both instances tested (n=2) —
possibly a distinct weakness in date-boundary reasoning, not yet
confirmed with enough data to state confidently.

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

Add your API keys to `.env`, then run:

```
uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## References

- Reliability without Validity: A Systematic, Large-Scale Evaluation of
  LLM-as-a-Judge Models — [arxiv.org/abs/2606.19544](https://arxiv.org/abs/2606.19544)
- The Coin Flip Judge? Reliability and Bias in LLM-as-a-Judge Evaluation
  — [arxiv.org/pdf/2606.13685](https://arxiv.org/pdf/2606.13685)
- CyclicJudge: Mitigating Judge Bias Efficiently in LLM-based Evaluation
  — [arxiv.org/pdf/2603.01865](https://arxiv.org/pdf/2603.01865)
- JUDGe 2026 — Can We Trust the Judge? —
  [judge2026.github.io](https://judge2026.github.io/)