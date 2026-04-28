from stocksense.core.sec_edgar import (
    build_filing_archive_url,
    extract_company_fact_metrics,
    resolve_cik_for_ticker,
    select_recent_filings,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def json(self):
        return self.payload

    def raise_for_status(self):
        return None


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def get(self, url):
        return FakeResponse(self.payload)


def test_resolve_cik_for_ticker_normalizes_company_ticker_payload(monkeypatch):
    payload = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 2488, "ticker": "AMD", "title": "Advanced Micro Devices"},
    }
    monkeypatch.setattr("stocksense.core.sec_edgar.httpx.Client", lambda **kwargs: FakeClient(payload))

    assert resolve_cik_for_ticker("amd") == "0000002488"


def test_missing_ticker_returns_none(monkeypatch):
    payload = {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}}
    monkeypatch.setattr("stocksense.core.sec_edgar.httpx.Client", lambda **kwargs: FakeClient(payload))

    assert resolve_cik_for_ticker("ZZZZ") is None


def test_select_recent_filings_for_core_forms():
    submissions = {
        "cik": "0000002488",
        "tickers": ["AMD"],
        "filings": {
            "recent": {
                "form": ["4", "10-Q", "8-K", "10-K"],
                "accessionNumber": ["a", "0000002488-26-000010", "0000002488-26-000009", "0000002488-25-000111"],
                "filingDate": ["2026-04-01", "2026-03-01", "2026-02-01", "2025-12-31"],
                "reportDate": ["", "2026-02-28", "2026-02-01", "2025-12-31"],
                "primaryDocument": ["x.htm", "amd-10q.htm", "amd-8k.htm", "amd-10k.htm"],
            }
        },
    }

    filings = select_recent_filings(submissions, limit=3)

    assert [filing.filing_type for filing in filings] == ["10-Q", "8-K", "10-K"]
    assert filings[0].filing_url.endswith("/2488/000000248826000010/amd-10q.htm")


def test_extract_company_fact_metrics_for_common_metrics():
    facts = {
        "facts": {
            "us-gaap": {
                "Revenues": {
                    "units": {
                        "USD": [
                            {"val": 10, "end": "2025-12-31", "filed": "2026-01-31", "form": "10-K", "accn": "old"},
                            {"val": 15, "end": "2026-03-31", "filed": "2026-04-25", "form": "10-Q", "accn": "new"},
                        ]
                    }
                },
                "GrossProfit": {"units": {"USD": [{"val": 6, "end": "2026-03-31", "filed": "2026-04-25"}]}},
                "OperatingIncomeLoss": {"units": {"USD": [{"val": 3, "end": "2026-03-31", "filed": "2026-04-25"}]}},
                "NetIncomeLoss": {"units": {"USD": [{"val": 2, "end": "2026-03-31", "filed": "2026-04-25"}]}},
                "CashAndCashEquivalentsAtCarryingValue": {
                    "units": {"USD": [{"val": 7, "end": "2026-03-31", "filed": "2026-04-25"}]}
                },
                "LongTermDebt": {"units": {"USD": [{"val": 4, "end": "2026-03-31", "filed": "2026-04-25"}]}},
            },
            "dei": {
                "EntityCommonStockSharesOutstanding": {
                    "units": {"shares": [{"val": 100, "end": "2026-03-31", "filed": "2026-04-25"}]}
                }
            },
        }
    }

    metrics = extract_company_fact_metrics(facts)
    by_key = {metric["metric_key"]: metric for metric in metrics}

    assert by_key["revenue"]["value"] == 15
    assert by_key["gross_profit"]["value"] == 6
    assert by_key["operating_income"]["value"] == 3
    assert by_key["net_income"]["value"] == 2
    assert by_key["cash"]["value"] == 7
    assert by_key["debt"]["value"] == 4
    assert by_key["shares"]["value"] == 100


def test_build_filing_archive_url_returns_none_when_document_missing():
    assert build_filing_archive_url("0000002488", "0000002488-26-000010", None) is None
