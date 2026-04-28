"""
Small SEC EDGAR adapter for Research Room evidence collection.

The adapter keeps network fetches deterministic and parseable. LLM agents get
normalized facts and filing metadata, never raw SEC response plumbing.
"""

from __future__ import annotations

import os
from typing import Any, Iterable

import httpx

from stocksense.core.research_schemas import SecFilingMetadata


SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_ARCHIVE_BASE_URL = "https://www.sec.gov/Archives/edgar/data"


class SecEdgarError(RuntimeError):
    """Raised for SEC transport or parsing failures."""


def get_sec_user_agent() -> str:
    return os.getenv("SEC_USER_AGENT", "StockSense-Agent/0.1 contact@example.com")


def normalize_cik(cik: str | int) -> str:
    return str(cik).strip().zfill(10)


def _archive_cik(cik: str | int) -> str:
    return str(int(str(cik).strip()))


def _client() -> httpx.Client:
    return httpx.Client(timeout=10.0, headers={"User-Agent": get_sec_user_agent()})


def _json_response(response: httpx.Response) -> Any:
    if hasattr(response, "raise_for_status"):
        response.raise_for_status()
    return response.json()


def fetch_company_tickers() -> list[dict[str, Any]]:
    with _client() as client:
        payload = _json_response(client.get(SEC_COMPANY_TICKERS_URL))

    rows = payload.values() if isinstance(payload, dict) else payload
    companies: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker", "")).upper().strip()
        cik = row.get("cik_str")
        if ticker and cik is not None:
            companies.append(
                {
                    "ticker": ticker,
                    "cik": normalize_cik(cik),
                    "title": row.get("title"),
                }
            )
    return companies


def resolve_cik_for_ticker(ticker: str) -> str | None:
    wanted = ticker.upper().strip()
    try:
        for company in fetch_company_tickers():
            if company["ticker"] == wanted:
                return company["cik"]
    except Exception as exc:
        raise SecEdgarError(f"SEC ticker lookup failed for {wanted}: {exc}") from exc
    return None


def fetch_company_submissions(cik: str) -> dict[str, Any]:
    with _client() as client:
        return _json_response(client.get(SEC_SUBMISSIONS_URL.format(cik=normalize_cik(cik))))


def fetch_company_facts(cik: str) -> dict[str, Any]:
    with _client() as client:
        return _json_response(client.get(SEC_COMPANY_FACTS_URL.format(cik=normalize_cik(cik))))


def build_filing_archive_url(cik: str, accession_number: str, primary_document: str | None) -> str | None:
    if not accession_number or not primary_document:
        return None
    accession_path = accession_number.replace("-", "")
    return f"{SEC_ARCHIVE_BASE_URL}/{_archive_cik(cik)}/{accession_path}/{primary_document}"


def select_recent_filings(
    submissions: dict[str, Any],
    forms: Iterable[str] = ("10-K", "10-Q", "8-K"),
    limit: int = 6,
) -> list[SecFilingMetadata]:
    recent = (submissions.get("filings") or {}).get("recent") or {}
    accepted_forms = {form.upper() for form in forms}
    ticker = (submissions.get("tickers") or [""])[0] if isinstance(submissions.get("tickers"), list) else ""
    cik = normalize_cik(submissions.get("cik", ""))

    form_values = recent.get("form") or []
    accession_values = recent.get("accessionNumber") or []
    filing_dates = recent.get("filingDate") or []
    report_dates = recent.get("reportDate") or []
    primary_documents = recent.get("primaryDocument") or []

    filings: list[SecFilingMetadata] = []
    for index, filing_type in enumerate(form_values):
        if str(filing_type).upper() not in accepted_forms:
            continue
        accession_number = accession_values[index] if index < len(accession_values) else ""
        primary_document = primary_documents[index] if index < len(primary_documents) else None
        filings.append(
            SecFilingMetadata(
                cik=cik,
                ticker=str(ticker).upper(),
                accession_number=accession_number,
                filing_type=str(filing_type).upper(),
                filing_date=filing_dates[index] if index < len(filing_dates) else "",
                report_date=report_dates[index] if index < len(report_dates) else None,
                primary_document=primary_document,
                filing_url=build_filing_archive_url(cik, accession_number, primary_document),
            )
        )
        if len(filings) >= limit:
            break
    return filings


FACT_METRICS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "revenue": (
        "Revenue",
        ("us-gaap",),
        (
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "Revenues",
            "SalesRevenueNet",
        ),
    ),
    "gross_profit": ("Gross profit", ("us-gaap",), ("GrossProfit",)),
    "operating_income": ("Operating income", ("us-gaap",), ("OperatingIncomeLoss",)),
    "net_income": ("Net income", ("us-gaap",), ("NetIncomeLoss", "ProfitLoss")),
    "cash": (
        "Cash and equivalents",
        ("us-gaap",),
        ("CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"),
    ),
    "debt": ("Debt", ("us-gaap",), ("LongTermDebt", "LongTermDebtAndFinanceLeaseObligationsCurrentAndNoncurrent")),
    "shares": ("Shares outstanding", ("dei",), ("EntityCommonStockSharesOutstanding",)),
}


def _sort_fact_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        [entry for entry in entries if entry.get("val") is not None],
        key=lambda entry: (entry.get("end") or "", entry.get("filed") or ""),
        reverse=True,
    )


def _latest_fact(facts: dict[str, Any], namespaces: tuple[str, ...], concepts: tuple[str, ...]) -> dict[str, Any] | None:
    facts_root = facts.get("facts") or {}
    for namespace in namespaces:
        namespace_facts = facts_root.get(namespace) or {}
        for concept in concepts:
            fact = namespace_facts.get(concept)
            units = (fact or {}).get("units") or {}
            preferred_units = ["USD", "shares", "pure"] + sorted(units.keys())
            for unit in preferred_units:
                if unit not in units:
                    continue
                entries = _sort_fact_entries(units.get(unit) or [])
                if entries:
                    latest = dict(entries[0])
                    latest["unit"] = unit
                    latest["concept"] = concept
                    return latest
    return None


def extract_company_fact_metrics(facts: dict[str, Any]) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    for metric_key, (label, namespaces, concepts) in FACT_METRICS.items():
        entry = _latest_fact(facts, namespaces, concepts)
        if not entry:
            continue
        metrics.append(
            {
                "metric_key": metric_key,
                "label": label,
                "value": entry.get("val"),
                "unit": entry.get("unit"),
                "period": entry.get("end"),
                "filed_at": entry.get("filed"),
                "form": entry.get("form"),
                "accession_number": entry.get("accn"),
                "concept": entry.get("concept"),
            }
        )
    return metrics
