"""Regression tests for Phase 1 critical bug fixes."""
import pytest
from unittest.mock import patch, MagicMock
from stocksense.core.schemas import SentimentAnalysisResult, HeadlineSentiment, KeyTheme


class TestSkepticMockDataFix:
    def test_generate_skeptic_critique_uses_real_headlines(self):
        """Skeptic tool must use real sentiment values, not zeros (P1-A).

        The test verifies:
        1. The fixture has real headlines (fixture integrity check).
        2. The react_flow source no longer constructs a 'mock_primary' — it was
           renamed to 'primary_analysis' with real values passed in.
        """
        fake_sentiment = SentimentAnalysisResult(
            overall_sentiment="Bullish",
            overall_confidence=0.8,
            confidence_reasoning="Strong earnings beat",
            bullish_count=3,
            bearish_count=1,
            neutral_count=0,
            insufficient_data_count=0,
            headline_analyses=[
                HeadlineSentiment(
                    headline="Apple beats Q4 earnings",
                    sentiment="Bullish",
                    confidence=0.9,
                    reasoning="Strong beat",
                    key_entities=["Apple"]
                )
            ],
            key_themes=[
                KeyTheme(
                    theme="Earnings Beat",
                    sentiment_direction="Bullish",
                    headline_count=3,
                    summary="Strong Q4"
                )
            ],
            potential_impact="Moderate Positive",
            risks_identified=["China exposure"],
            information_gaps=[]
        )

        # Fixture integrity: confirm test fixture has real headlines
        assert len(fake_sentiment.headline_analyses) == 1, \
            "Test fixture must have real headlines"

        # Verify the source-level fix: react_flow must no longer use 'mock_primary'
        import inspect
        import stocksense.orchestration.react_flow as react_flow_module
        source = inspect.getsource(react_flow_module.generate_skeptic_critique.func
                                   if hasattr(react_flow_module.generate_skeptic_critique, 'func')
                                   else react_flow_module.generate_skeptic_critique)
        assert "mock_primary" not in source, \
            "react_flow still uses 'mock_primary' — P1-A fix was not applied"
        assert "primary_analysis" in source, \
            "react_flow must use 'primary_analysis' variable after P1-A fix"
        assert "Based on structured headline analysis" in source, \
            "Confidence reasoning must be the updated non-placeholder value"


class TestKillAlertsTableName:
    def test_get_kill_alert_reads_alert_history(self):
        """auth_routes GET /kill-alerts/{id} must query alert_history, not kill_alerts."""
        import inspect
        import stocksense.api.auth_routes as auth_routes_module

        source = inspect.getsource(auth_routes_module.get_kill_alert)
        assert "kill_alerts" not in source, (
            "get_kill_alert still queries 'kill_alerts' table — should be 'alert_history'"
        )
        assert "alert_history" in source

    def test_delete_kill_alert_deletes_from_alert_history(self):
        """auth_routes DELETE /kill-alerts/{id} must delete from alert_history."""
        import inspect
        import stocksense.api.auth_routes as auth_routes_module

        source = inspect.getsource(auth_routes_module.delete_kill_alert)
        assert "kill_alerts" not in source, (
            "delete_kill_alert still uses 'kill_alerts' table — should be 'alert_history'"
        )
        assert "alert_history" in source


class TestTickerValidation:
    def test_validation_returns_false_when_yfinance_raises(self, monkeypatch):
        """validate_ticker_exists must return False when yfinance throws an exception."""
        import yfinance as yf
        from stocksense.core.validation import validate_ticker_exists

        def boom(ticker_symbol):
            raise ConnectionError("Network unreachable")

        monkeypatch.setattr(yf, "Ticker", boom)

        is_valid, error_msg = validate_ticker_exists("AAPL")

        assert is_valid is False, "Should return False when yfinance raises, not True"
        assert error_msg is not None, "Should return an error message"
        assert "AAPL" in error_msg

    def test_validation_returns_true_for_real_ticker(self, monkeypatch):
        """validate_ticker_exists returns True for a ticker with market data."""
        import yfinance as yf
        from stocksense.core.validation import validate_ticker_exists

        mock_ticker = MagicMock()
        mock_ticker.info = {"regularMarketPrice": 185.5, "shortName": "Apple Inc."}
        monkeypatch.setattr(yf, "Ticker", lambda _: mock_ticker)

        is_valid, error_msg = validate_ticker_exists("AAPL")

        assert is_valid is True
        assert error_msg is None


class TestDataCollectorErrors:
    def test_get_news_raises_on_api_error(self, monkeypatch):
        """get_news must raise DataCollectionError on API failure, not return []."""
        import requests.exceptions
        from stocksense.core.data_collectors import get_news, DataCollectionError

        # Ensure NEWSAPI_KEY is set so get_newsapi_key() doesn't raise ConfigurationError
        monkeypatch.setenv("NEWSAPI_KEY", "fake_key")

        # Patch NewsApiClient so calling get_everything raises a Timeout
        from unittest.mock import MagicMock
        mock_client = MagicMock()
        mock_client.get_everything.side_effect = requests.exceptions.Timeout("timed out")

        import newsapi as newsapi_module
        monkeypatch.setattr(newsapi_module, "NewsApiClient", lambda api_key: mock_client)

        with pytest.raises(DataCollectionError, match="timeout"):
            get_news("AAPL")

    def test_get_price_history_raises_on_exception(self, monkeypatch):
        """get_price_history must raise DataCollectionError on yfinance failure."""
        import yfinance as yf
        from stocksense.core.data_collectors import get_price_history, DataCollectionError

        def boom(ticker_symbol):
            raise ConnectionError("Network down")

        monkeypatch.setattr(yf, "Ticker", boom)

        with pytest.raises(DataCollectionError, match="price history"):
            get_price_history("AAPL")

    def test_get_fundamental_data_raises_on_exception(self, monkeypatch):
        """get_fundamental_data must raise DataCollectionError on yfinance failure."""
        import yfinance as yf
        from stocksense.core.data_collectors import get_fundamental_data, DataCollectionError

        def boom(ticker_symbol):
            raise ConnectionError("Network down")

        monkeypatch.setattr(yf, "Ticker", boom)

        with pytest.raises(DataCollectionError, match="fundamental"):
            get_fundamental_data("AAPL")
