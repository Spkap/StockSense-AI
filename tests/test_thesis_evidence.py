import asyncio
import time
from unittest.mock import patch

from stocksense.orchestration.thesis_evidence import collect_evidence_for_ticker


def test_collect_evidence_runs_sources_and_returns_bundle():
    with patch("stocksense.orchestration.thesis_evidence.get_news", return_value=["Apple beats earnings"]):
        with patch("stocksense.orchestration.thesis_evidence.get_price_history", return_value=None):
            with patch(
                "stocksense.orchestration.thesis_evidence.get_fundamental_data",
                return_value={"info": {"market_cap": 100}},
            ):
                bundle = asyncio.run(collect_evidence_for_ticker("AAPL"))

    assert bundle.ticker == "AAPL"
    assert len(bundle.evidence) == 2
    assert {item.source_type for item in bundle.evidence} == {"news", "fundamentals"}


def test_collect_evidence_records_source_failure_without_crashing():
    def failing_news(*args, **kwargs):
        raise RuntimeError("news down")

    with patch("stocksense.orchestration.thesis_evidence.get_news", side_effect=failing_news):
        with patch("stocksense.orchestration.thesis_evidence.get_price_history", return_value=None):
            with patch("stocksense.orchestration.thesis_evidence.get_fundamental_data", return_value={}):
                bundle = asyncio.run(collect_evidence_for_ticker("MSFT"))

    news_status = [status for status in bundle.source_statuses if status.source_type == "news"][0]
    assert news_status.status == "failed"
    assert "news down" in news_status.error


def test_collect_evidence_finishes_near_slowest_source_not_sum():
    def slow_news(*args, **kwargs):
        time.sleep(0.2)
        return ["Microsoft announces product"]

    def slow_price(*args, **kwargs):
        time.sleep(0.2)
        return None

    def slow_fundamentals(*args, **kwargs):
        time.sleep(0.2)
        return {}

    start = time.monotonic()
    with patch("stocksense.orchestration.thesis_evidence.get_news", side_effect=slow_news):
        with patch("stocksense.orchestration.thesis_evidence.get_price_history", side_effect=slow_price):
            with patch("stocksense.orchestration.thesis_evidence.get_fundamental_data", side_effect=slow_fundamentals):
                asyncio.run(collect_evidence_for_ticker("MSFT"))
    duration = time.monotonic() - start

    assert duration < 0.45
