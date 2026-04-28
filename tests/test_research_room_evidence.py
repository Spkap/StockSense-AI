import asyncio
from unittest.mock import patch

from stocksense.orchestration.research_room_evidence import collect_research_evidence


def test_collect_research_evidence_continues_when_sec_fails():
    with patch("stocksense.orchestration.research_room_evidence.resolve_cik_for_ticker", side_effect=RuntimeError("sec down")):
        with patch("stocksense.orchestration.research_room_evidence.get_price_history", return_value=None):
            with patch(
                "stocksense.orchestration.research_room_evidence.get_fundamental_data",
                return_value={"info": {"market_cap": 100, "revenue_growth": 0.2}},
            ):
                with patch("stocksense.orchestration.research_room_evidence.get_news", return_value=["AMD launches AI chip"]):
                    bundle = asyncio.run(collect_research_evidence("amd", "AI server thesis?"))

    statuses = {status.source_type: status.status for status in bundle.source_statuses}
    assert statuses["sec_submissions"] == "failed"
    assert statuses["sec_company_facts"] == "failed"
    assert any(item.source_type == "fundamentals" for item in bundle.evidence)
    assert any(item.source_type == "news" for item in bundle.evidence)
    assert bundle.company_snapshot["sec_gap"] is True


def test_collect_research_evidence_converts_sec_sources_to_high_reliability_evidence():
    submissions = {
        "cik": "0000002488",
        "tickers": ["AMD"],
        "filings": {
            "recent": {
                "form": ["10-Q"],
                "accessionNumber": ["0000002488-26-000010"],
                "filingDate": ["2026-04-25"],
                "reportDate": ["2026-03-31"],
                "primaryDocument": ["amd-10q.htm"],
            }
        },
    }
    facts = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [{"val": 10, "end": "2026-03-31", "filed": "2026-04-25", "form": "10-Q"}]
                    }
                }
            }
        }
    }

    with patch("stocksense.orchestration.research_room_evidence.resolve_cik_for_ticker", return_value="0000002488"):
        with patch("stocksense.orchestration.research_room_evidence.fetch_company_submissions", return_value=submissions):
            with patch("stocksense.orchestration.research_room_evidence.fetch_company_facts", return_value=facts):
                with patch("stocksense.orchestration.research_room_evidence.get_price_history", return_value=None):
                    with patch("stocksense.orchestration.research_room_evidence.get_fundamental_data", return_value={}):
                        with patch("stocksense.orchestration.research_room_evidence.get_news", return_value=[]):
                            bundle = asyncio.run(collect_research_evidence("AMD", "AI server thesis?"))

    evidence_by_id = {item.local_id: item for item in bundle.evidence}
    assert "sec_10q_01" in evidence_by_id
    assert "fact_revenue_01" in evidence_by_id
    assert evidence_by_id["sec_10q_01"].reliability_tier == "high"
    assert evidence_by_id["fact_revenue_01"].source_type == "sec_company_facts"
