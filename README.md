# Renewal Risk Agent

An agent that assesses whether a B2B SaaS customer account is at risk of
churning before renewal, using usage data, support ticket history, and
contract terms. Built with LangGraph and served via FastAPI.

The project also includes a judge integrity toolkit that validates the
reliability of the LLM judge used to score the agent's outputs — checking
for position bias, run-to-run consistency, and calibration against
human-labeled cases — rather than assuming the judge's verdicts can be
trusted by default.

Live demo: [renewal-risk-agent.onrender.com](https://renewal-risk-agent.onrender.com). Pick an
account, run the agent, and compare its verdict with the golden-set label. The free instance
sleeps when idle, so the first load can take about a minute.

API: `GET /predict/renewal-risk/?customer_id=cust_001` (cust_001 to cust_020), `GET /customers/`
for the raw signals and labels, and interactive docs at `/docs`.

## Repository Structure

```
renewal-risk-agent/
├── src/
│   ├── main.py              <- FastAPI entrypoint (API + demo page)
│   ├── static/index.html     <- Demo UI, served at /
│   ├── config.py             <- Settings, loaded from environment
│   ├── agent.py              <- LangGraph ReAct agent
│   ├── tools.py               <- Tools available to the agent
│   ├── tracing.py             <- OpenTelemetry / Phoenix instrumentation
│   ├── eval/                  <- Golden-set evaluation (DeepEval / RAGAS)
│   └── judge_validator/       <- Judge reliability checks
├── data/golden_set/          <- Curated evaluation cases
├── tests/                     <- pytest suite
├── .github/workflows/         <- CI: lint, tests, Docker smoke test; evals on demand
├── Dockerfile                 <- slim serving image (no eval tooling)
├── Makefile                   <- install / test / lint / run / evals / lock
├── requirements.in / .txt     <- serving deps (source / pinned lock)
├── requirements-dev.in / .txt <- adds pytest, ruff, DeepEval, scikit-learn
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

**Model note:** the findings above were measured with Groq `llama-3.3-70b-versatile`, which
Groq retired in August 2026. The agent now defaults to `openai/gpt-oss-120b` on Groq with Gemini
as an automatic fallback. Re-running the golden set and the flip-rate check on the new model is
the next experiment, and a useful one: it tests whether the judge findings hold across models.

**Open hypothesis, weaker evidence:** cases where the renewal date falls
exactly on the current day failed in both instances tested (n=2) —
possibly a distinct weakness in date-boundary reasoning, not yet
confirmed with enough data to state confidently.

## Running it

```
git clone https://github.com/Nidhi313/renewal-risk-agent.git
cd renewal-risk-agent
pip install -r requirements-dev.txt
cp .env.example .env        # add GROQ_API_KEY and/or GOOGLE_API_KEY
make run                    # http://localhost:8080
make test                   # no API keys or tokens needed
make evals                  # golden set through the agent + DeepEval judge (real LLM calls)
```

Docker: `make docker`. The image only carries serving dependencies (about 120 MB of RAM at
idle), so it fits Render's free 512 MB instance.

## Model providers and free-tier limits

Model IDs are environment variables (`GROQ_MODEL`, `GEMINI_MODEL`), so a provider retiring a
model is a config change, not a code change. If the primary provider (`MODEL_PROVIDER`) errors
on a rate limit, a retired model, or a missing key, the request is retried once on
`FALLBACK_PROVIDER`. Assessments are cached per customer per day, because the synthetic data
does not change and repeated demo clicks would otherwise burn quota.

## Deploying to Render

The live demo runs as a Docker web service on Render that redeploys on every push to `main`.
In the service's Environment tab, set `GROQ_API_KEY` and `GOOGLE_API_KEY`; the other settings in
`.env.example` have working defaults. Health check path: `/health/`.

## References

- Reliability without Validity: A Systematic, Large-Scale Evaluation of
  LLM-as-a-Judge Models — [arxiv.org/abs/2606.19544](https://arxiv.org/abs/2606.19544)
- The Coin Flip Judge? Reliability and Bias in LLM-as-a-Judge Evaluation
  — [arxiv.org/pdf/2606.13685](https://arxiv.org/pdf/2606.13685)
- CyclicJudge: Mitigating Judge Bias Efficiently in LLM-based Evaluation
  — [arxiv.org/pdf/2603.01865](https://arxiv.org/pdf/2603.01865)
- JUDGe 2026 — Can We Trust the Judge? —
  [judge2026.github.io](https://judge2026.github.io/)