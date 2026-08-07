"""Run the golden set through the agent and score with DeepEval.

Usage: python -m src.eval.run_evals
"""
import json
import sys
import warnings
from pathlib import Path

from deepeval.metrics import GEval
from deepeval.models import GeminiModel, OllamaModel
from deepeval.models.base_model import DeepEvalBaseLLM
from langchain_groq import ChatGroq
from deepeval.test_case import LLMTestCase, SingleTurnParams

from src.agent import assess_customer
from src.config import settings

# Suppress noisy library warnings that don't affect correctness --
# real errors are still caught and shown explicitly below.
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*fixed sampling defaults.*")

GOLDEN_SET_PATH = Path(__file__).parent.parent.parent / "data" / "golden_set" / "cases.jsonl"

class GroqJudge(DeepEvalBaseLLM):
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.model_name = model_name
        self.model = ChatGroq(model=model_name, temperature=0, api_key=settings.groq_api_key)

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        return self.load_model().invoke(prompt).content

    async def a_generate(self, prompt: str) -> str:
        res = await self.load_model().ainvoke(prompt)
        return res.content

    def get_model_name(self):
        return self.model_name

if settings.model_provider == "ollama":
    judge_model = OllamaModel(model="llama3.2", base_url="http://localhost:11434", temperature=0)
elif settings.model_provider == "groq":
    judge_model = GroqJudge()
else:
    judge_model = GeminiModel(model="gemini-3.6-flash", api_key=settings.google_api_key, temperature=0)

verdict_correctness = GEval(
    name="Verdict Correctness",
    criteria=(
        "Determine whether the actual output's risk verdict and reasoning "
        "are consistent with the expected verdict and reasoning keywords. "
        "The agent does not need to use identical wording, but the "
        "substance of its conclusion must match."
    ),
    evaluation_params=[
        SingleTurnParams.INPUT,
        SingleTurnParams.ACTUAL_OUTPUT,
        SingleTurnParams.EXPECTED_OUTPUT,
    ],
    model=judge_model,
    threshold=0.7,
)


def load_golden_set() -> list[dict]:
    cases = []
    with open(GOLDEN_SET_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def run_eval_suite():
    cases = load_golden_set()
    results = []

    print(f"\nRunning {len(cases)} golden set cases (judge: {settings.model_provider})\n" + "-" * 60)

    for case in cases:
        case_id, customer_id = case["case_id"], case["customer_id"]

        try:
            actual_output = assess_customer(customer_id)
        except Exception as e:
            print(f"  {case_id:<10} ({customer_id})  ERROR (agent)   {type(e).__name__}: {str(e)[:80]}")
            results.append({"case_id": case_id, "passed": False, "score": 0.0, "is_edge_case": case["is_edge_case"]})
            continue

        expected_output = (
            f"Expected verdict: {case['expected_verdict']}. "
            f"Should reference: {', '.join(case['expected_reasoning_keywords'])}."
        )
        test_case = LLMTestCase(
            input=f"Assess renewal risk for {customer_id}",
            actual_output=actual_output,
            expected_output=expected_output,
        )

        try:
            verdict_correctness.measure(test_case)
            passed, score = verdict_correctness.is_successful(), verdict_correctness.score
        except Exception as e:
            print(f"  {case_id:<10} ({customer_id})  ERROR (judge)   {type(e).__name__}: {str(e)[:80]}")
            results.append({"case_id": case_id, "passed": False, "score": 0.0, "is_edge_case": case["is_edge_case"]})
            continue

        status = "PASS" if passed else "FAIL"
        edge = " [edge case]" if case["is_edge_case"] else ""
        print(f"  {case_id:<10} ({customer_id})  {status:<5} score={score:.2f}{edge}")
        results.append({"case_id": case_id, "passed": passed, "score": score, "is_edge_case": case["is_edge_case"]})

    print("-" * 60)
    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    pass_rate = passed_count / total if total else 0.0
    edge_total = sum(1 for r in results if r["is_edge_case"])
    edge_passed = sum(1 for r in results if r["is_edge_case"] and r["passed"])

    print(f"\nSummary: {passed_count}/{total} passed ({pass_rate:.0%})")
    if edge_total:
        print(f"  Edge cases: {edge_passed}/{edge_total} passed")
    failed = [r["case_id"] for r in results if not r["passed"]]
    if failed:
        print(f"  Failed: {', '.join(failed)}")

    if pass_rate < 0.7:
        print("\nFAILED: pass rate below 70% threshold.")
        sys.exit(1)

    print("\nPASSED: eval suite meets quality threshold.")


if __name__ == "__main__":
    run_eval_suite()