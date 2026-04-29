"""Tests for Phase 2 — Impressive Engineering features."""
import pytest
from unittest.mock import MagicMock


# =============================================================================
# Task 1: Correlation ID Middleware (P2-D)
# =============================================================================

class TestCorrelationMiddleware:
    def test_response_has_correlation_id_header(self):
        """Every response must include X-Correlation-ID header."""
        from fastapi.testclient import TestClient
        from stocksense.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers, (
            "X-Correlation-ID header missing from /health response"
        )

    def test_correlation_id_is_8_chars(self):
        """Correlation ID must be exactly 8 hex characters."""
        from fastapi.testclient import TestClient
        from stocksense.main import app
        client = TestClient(app)
        response = client.get("/health")
        cid = response.headers.get("X-Correlation-ID", "")
        assert len(cid) == 8, f"Expected 8-char correlation ID, got: '{cid}'"

    def test_each_request_gets_unique_id(self):
        """Two requests must get different correlation IDs."""
        from fastapi.testclient import TestClient
        from stocksense.main import app
        client = TestClient(app)
        r1 = client.get("/health")
        r2 = client.get("/health")
        cid1 = r1.headers.get("X-Correlation-ID")
        cid2 = r2.headers.get("X-Correlation-ID")
        assert cid1 != cid2, "Two requests got the same correlation ID — not random"


# =============================================================================
# Task 2: Cache TTL + Upsert (P2-E)
# =============================================================================

class TestCacheTTL:
    def test_get_latest_analysis_returns_none_for_stale_cache(self, monkeypatch):
        """get_latest_analysis must return None when cached row is older than 24h."""
        from stocksense.db import database

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value \
            .data = []  # gte filter returns empty — nothing within 24h

        monkeypatch.setattr(database, "get_supabase_client", lambda: mock_client)

        result = database.get_latest_analysis("AAPL")
        assert result is None, "Should return None for stale cache (>24h old)"

    def test_get_latest_analysis_returns_data_within_24h(self, monkeypatch):
        """get_latest_analysis returns data when cached row is fresh (<24h)."""
        from stocksense.db import database

        from datetime import datetime, timezone, timedelta
        fresh_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        fake_row = {
            "id": "abc123",
            "ticker": "AAPL",
            "analysis_summary": "Bullish",
            "sentiment_report": "positive",
            "created_at": fresh_time,
            "price_data": [],
            "headlines": [],
            "reasoning_steps": [],
            "tools_used": [],
            "iterations": 3,
            "overall_sentiment": "Bullish",
            "overall_confidence": 0.75,
            "confidence_reasoning": "strong",
            "headline_analyses": [],
            "key_themes": [],
            "potential_impact": "positive",
            "risks_identified": [],
            "information_gaps": [],
            "skeptic_report": "",
            "skeptic_sentiment": "",
            "skeptic_confidence": 0.0,
            "primary_disagreement": "",
            "critiques": [],
            "bear_cases": [],
            "hidden_risks": [],
            "would_change_mind": [],
            "fundamental_data": {},
        }

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value \
            .eq.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value \
            .data = [fake_row]

        monkeypatch.setattr(database, "get_supabase_client", lambda: mock_client)

        result = database.get_latest_analysis("AAPL")
        assert result is not None, "Should return data for fresh cache (<24h)"
        assert result["ticker"] == "AAPL"

    def test_save_analysis_calls_upsert_not_insert(self, monkeypatch):
        """save_analysis must call upsert (not insert) to avoid duplicate rows."""
        from stocksense.db import database

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value.data = [{"id": "x1"}]

        monkeypatch.setattr(database, "get_supabase_admin_client", lambda: mock_client)

        database.save_analysis(ticker="AAPL", summary="test", sentiment_report="bullish")

        mock_table.upsert.assert_called_once()
        mock_table.insert.assert_not_called()

    def test_save_analysis_sanitizes_nan_for_json_storage(self, monkeypatch):
        """save_analysis must convert NaN/Infinity payload values to None."""
        from stocksense.db import database

        mock_client = MagicMock()
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        mock_table.upsert.return_value.execute.return_value.data = [{"id": "x1"}]

        monkeypatch.setattr(database, "get_supabase_admin_client", lambda: mock_client)

        database.save_analysis(
            ticker="AAPL",
            summary="test",
            sentiment_report="bullish",
            price_data=[{"Close": float("nan"), "Volume": 100}],
            fundamental_data={"info": {"market_cap": float("inf"), "beta": 1.2}},
            overall_confidence=float("nan"),
        )

        upsert_payload = mock_table.upsert.call_args.args[0]
        assert upsert_payload["overall_confidence"] is None
        assert upsert_payload["price_data"][0]["Close"] is None
        assert upsert_payload["fundamental_data"]["info"]["market_cap"] is None


# =============================================================================
# Task 3: Technical Analysis Signals (P3-N)
# =============================================================================

class TestTechnicalAnalysis:
    def _make_price_data(self, closes: list) -> list:
        """Build minimal OHLCV dicts for testing."""
        from datetime import date, timedelta
        base = date(2026, 1, 1)
        return [
            {"date": str(base + timedelta(days=i)), "close": c, "volume": 1_000_000}
            for i, c in enumerate(closes)
        ]

    def test_compute_technical_signals_returns_expected_keys(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        prices = self._make_price_data([100.0 + i * 0.5 for i in range(60)])
        result = compute_technical_signals(prices)
        assert "trend" in result
        assert "rsi" in result
        assert "rsi_signal" in result
        assert "annualized_volatility" in result
        assert "price_vs_sma20_pct" in result
        assert "sma20" in result
        assert "sma50" in result

    def test_uptrend_when_sma20_above_sma50(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        # Rising prices — SMA20 will be above SMA50
        prices = self._make_price_data([50.0 + i * 1.0 for i in range(60)])
        result = compute_technical_signals(prices)
        assert result["trend"] == "uptrend"

    def test_downtrend_when_sma20_below_sma50(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        # Falling prices — SMA20 will be below SMA50
        prices = self._make_price_data([110.0 - i * 1.0 for i in range(60)])
        result = compute_technical_signals(prices)
        assert result["trend"] == "downtrend"

    def test_rsi_overbought_signal(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        # Strongly rising prices → RSI near 100
        prices = self._make_price_data([50.0 + i * 3.0 for i in range(60)])
        result = compute_technical_signals(prices)
        assert result["rsi_signal"] == "overbought"

    def test_rsi_oversold_signal(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        # Strongly falling prices → RSI near 0
        prices = self._make_price_data([200.0 - i * 3.0 for i in range(60)])
        result = compute_technical_signals(prices)
        assert result["rsi_signal"] == "oversold"

    def test_returns_insufficient_for_short_series(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        # Only 5 data points — not enough for SMA50 or RSI14
        prices = self._make_price_data([100.0, 101.0, 99.0, 102.0, 103.0])
        result = compute_technical_signals(prices)
        assert result["trend"] == "insufficient_data"

    def test_empty_price_data_returns_insufficient(self):
        from stocksense.core.technical_analysis import compute_technical_signals
        result = compute_technical_signals([])
        assert result["trend"] == "insufficient_data"


# =============================================================================
# Task 4: Headline Asymmetry (P2-B)
# =============================================================================

class TestHeadlineAsymmetry:
    HEADLINES = [
        "Apple beats Q4 earnings expectations",        # bull signal
        "Apple faces regulatory investigation",         # bear signal
        "Apple launches new iPhone model",              # bull signal
        "Apple misses revenue forecast",                # bear signal
        "Apple announces dividend increase",            # bull signal
        "Analysts cut Apple price target",              # bear signal
        "Apple wins patent lawsuit",                    # neutral/bull
        "Apple supply chain disruption reported",       # bear signal
    ]

    def test_bull_filter_surfaces_positive_headlines_first(self):
        from stocksense.agents.bull_analyst import BullAnalyst
        bull = BullAnalyst()
        filtered = bull.filter_headlines_for_perspective(self.HEADLINES)
        # First headline in result should be a bull signal
        assert any(
            w in filtered[0].lower()
            for w in ["beat", "launch", "dividend", "patent", "upgrade", "record"]
        ), f"Bull filter should surface positive news first, got: {filtered[0]}"

    def test_bear_filter_surfaces_negative_headlines_first(self):
        from stocksense.agents.bear_analyst import BearAnalyst
        bear = BearAnalyst()
        filtered = bear.filter_headlines_for_perspective(self.HEADLINES)
        # First headline in result should be a bear signal
        assert any(
            w in filtered[0].lower()
            for w in ["investigation", "miss", "cut", "disruption", "downgrade", "risk"]
        ), f"Bear filter should surface negative news first, got: {filtered[0]}"

    def test_filter_preserves_all_headlines(self):
        """No headlines are dropped — just reordered."""
        from stocksense.agents.bull_analyst import BullAnalyst
        bull = BullAnalyst()
        filtered = bull.filter_headlines_for_perspective(self.HEADLINES)
        assert set(filtered) == set(self.HEADLINES), "Filter must preserve all headlines"

    def test_bull_and_bear_get_different_orderings(self):
        """Bull and Bear must produce different headline orderings."""
        from stocksense.agents.bull_analyst import BullAnalyst
        from stocksense.agents.bear_analyst import BearAnalyst
        bull = BullAnalyst()
        bear = BearAnalyst()
        bull_order = bull.filter_headlines_for_perspective(self.HEADLINES)
        bear_order = bear.filter_headlines_for_perspective(self.HEADLINES)
        assert bull_order != bear_order, "Bull and Bear should prioritize different headlines"


# =============================================================================
# Task 5: Eval Harness (P3-K)
# =============================================================================

class TestEvalHarness:
    def test_golden_set_has_required_fields(self):
        """Every golden case must have ticker, mock_headlines, mock_fundamentals, and expectations."""
        from tests.evals.golden_set import GOLDEN_SET
        required_keys = {"ticker", "mock_headlines", "mock_fundamentals", "expectations"}
        for i, case in enumerate(GOLDEN_SET):
            missing = required_keys - set(case.keys())
            assert not missing, f"Golden case {i} missing fields: {missing}"

    def test_golden_set_has_at_least_5_cases(self):
        from tests.evals.golden_set import GOLDEN_SET
        assert len(GOLDEN_SET) >= 5, f"Need at least 5 golden cases, got {len(GOLDEN_SET)}"

    def test_eval_runner_is_importable(self):
        """eval_runner.py must import without errors."""
        from tests.evals import eval_runner  # noqa: F401

    def test_eval_report_schema(self):
        """EvalReport must have pass_count, fail_count, cases fields."""
        from tests.evals.eval_runner import EvalReport
        report = EvalReport(pass_count=3, fail_count=2, cases=[])
        assert report.pass_count == 3
        assert report.fail_count == 2
        assert report.cases == []
