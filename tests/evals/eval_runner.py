"""
Eval runner for StockSense agent quality.

Usage:
    .venv/bin/python tests/evals/eval_runner.py

Runs each case in GOLDEN_SET against the live Bull/Bear agents using mock data.
Produces a pass/fail report. Gate all prompt changes on this report.

DO NOT call live APIs (no NewsAPI, no yfinance). All data is from golden_set.py.
"""
from __future__ import annotations
import asyncio
import sys
import os
from dataclasses import dataclass, field
from typing import Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


@dataclass
class CaseResult:
    ticker: str
    passed: bool
    failures: list[str] = field(default_factory=list)
    bull_confidence: float = 0.0
    bear_confidence: float = 0.0
    bull_thesis: str = ""
    bear_thesis: str = ""


@dataclass
class EvalReport:
    pass_count: int
    fail_count: int
    cases: list[CaseResult]

    @property
    def pass_rate(self) -> float:
        total = self.pass_count + self.fail_count
        return self.pass_count / total if total > 0 else 0.0

    def print_report(self) -> None:
        print(f"\n{'='*60}")
        print(f"STOCKSENSE EVAL REPORT")
        print(f"{'='*60}")
        print(f"Pass rate: {self.pass_rate:.0%}  ({self.pass_count}/{self.pass_count + self.fail_count})")
        print()
        for case in self.cases:
            status = "✓ PASS" if case.passed else "✗ FAIL"
            print(f"  {status}  {case.ticker}")
            if not case.passed:
                for f in case.failures:
                    print(f"         → {f}")
            print(f"         Bull confidence: {case.bull_confidence:.2f}  |  Bear confidence: {case.bear_confidence:.2f}")
        print(f"{'='*60}\n")


async def run_single_case(case: dict[str, Any]) -> CaseResult:
    """Run one golden case with mocked data. No live API calls."""
    from stocksense.agents.bull_analyst import BullAnalyst
    from stocksense.agents.bear_analyst import BearAnalyst

    ticker = case["ticker"]
    headlines = case["mock_headlines"]
    fundamentals = case["mock_fundamentals"]
    price_data = case["mock_price_data"]
    exp = case["expectations"]

    # Minimal sentiment analysis (no live LLM call for eval)
    mock_sentiment = {
        "overall_sentiment": "Neutral",
        "overall_confidence": 0.5,
        "key_themes": [],
        "headline_analyses": [],
    }

    result = CaseResult(ticker=ticker, passed=True)
    failures = []

    bull = BullAnalyst()
    bear = BearAnalyst()

    # Run agents (these DO call live LLM — Gemini API must be available)
    try:
        bull_case = await bull.analyze(ticker, fundamentals, headlines, price_data, mock_sentiment)
        result.bull_confidence = bull_case.confidence if hasattr(bull_case, "confidence") else 0.0
        result.bull_thesis = bull_case.thesis if hasattr(bull_case, "thesis") else ""
    except Exception as e:
        failures.append(f"Bull agent failed: {e}")
        result.bull_confidence = 0.0

    try:
        bear_case = await bear.analyze(ticker, fundamentals, headlines, price_data, mock_sentiment)
        result.bear_confidence = bear_case.confidence if hasattr(bear_case, "confidence") else 0.0
        result.bear_thesis = bear_case.thesis if hasattr(bear_case, "thesis") else ""
    except Exception as e:
        failures.append(f"Bear agent failed: {e}")
        result.bear_confidence = 0.0

    # Check expectations
    if result.bull_confidence < exp["bull_confidence_min"]:
        failures.append(
            f"Bull confidence {result.bull_confidence:.2f} below min {exp['bull_confidence_min']}"
        )
    if result.bear_confidence < exp["bear_confidence_min"]:
        failures.append(
            f"Bear confidence {result.bear_confidence:.2f} below min {exp['bear_confidence_min']}"
        )
    if exp["bull_thesis_non_empty"] and not result.bull_thesis.strip():
        failures.append("Bull thesis is empty")
    if exp["bear_thesis_non_empty"] and not result.bear_thesis.strip():
        failures.append("Bear thesis is empty")

    result.failures = failures
    result.passed = len(failures) == 0
    return result


async def run_evals() -> EvalReport:
    from tests.evals.golden_set import GOLDEN_SET
    results = []
    for case in GOLDEN_SET:
        print(f"  Running {case['ticker']}...", end=" ", flush=True)
        result = await run_single_case(case)
        print("PASS" if result.passed else "FAIL")
        results.append(result)

    pass_count = sum(1 for r in results if r.passed)
    fail_count = len(results) - pass_count
    return EvalReport(pass_count=pass_count, fail_count=fail_count, cases=results)


if __name__ == "__main__":
    print("Running StockSense evals against golden set...")
    report = asyncio.run(run_evals())
    report.print_report()
    sys.exit(0 if report.pass_rate == 1.0 else 1)
