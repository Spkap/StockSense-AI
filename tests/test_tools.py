"""
Unit Tests for StockSense Agent Tools

All tests use deterministic mocks — zero live API calls.
Patch targets: stocksense.orchestration.react_flow.get_news
               stocksense.orchestration.react_flow.get_price_history
"""
import pytest
from unittest.mock import patch, MagicMock
from stocksense.orchestration.react_flow import fetch_news_headlines, fetch_price_data
from stocksense.core.data_collectors import DataCollectionError

# ── Fixtures ──────────────────────────────────────────────────────────────────

FAKE_HEADLINES = [
    "Apple beats Q4 earnings by $0.15 per share",
    "iPhone demand exceeds analyst expectations",
    "Apple faces EU antitrust investigation",
]


def _make_fake_price_df():
    """Build a fake DataFrame-like object that satisfies fetch_price_data's processing."""
    # fetch_price_data does:
    #   df.empty  -> False
    #   df.reset_index() -> df_reset
    #   df_reset['Date'].dt.strftime('%Y-%m-%d') -> list of date strings
    #   df_reset.to_dict(orient='records') -> list of dicts

    # We need a Series-like for df_reset['Date'] with a .dt accessor
    class _DateSeries:
        class _DT:
            def strftime(self, fmt):
                return ["2026-01-01", "2026-01-02"]
        dt = _DT()

    class _FakeDFReset:
        def __getitem__(self, key):
            if key == "Date":
                return _DateSeries()
            raise KeyError(key)

        def __setitem__(self, key, value):
            # fetch_price_data assigns: df_reset['Date'] = df_reset['Date'].dt.strftime(...)
            pass  # no-op, we ignore the assignment

        def to_dict(self, orient):
            return [
                {
                    "Date": "2026-01-01",
                    "Open": 218.0,
                    "High": 222.0,
                    "Low": 217.0,
                    "Close": 220.5,
                    "Volume": 1_200_000,
                },
                {
                    "Date": "2026-01-02",
                    "Open": 220.5,
                    "High": 224.0,
                    "Low": 219.0,
                    "Close": 223.0,
                    "Volume": 980_000,
                },
            ]

    class _FakePriceDF:
        empty = False

        def reset_index(self):
            return _FakeDFReset()

    return _FakePriceDF()


FAKE_PRICE_DATA_RAW = _make_fake_price_df()


@pytest.fixture
def mock_news():
    with patch("stocksense.orchestration.react_flow.get_news", return_value=FAKE_HEADLINES) as m:
        yield m


@pytest.fixture
def mock_price():
    with patch("stocksense.orchestration.react_flow.get_price_history", return_value=FAKE_PRICE_DATA_RAW) as m:
        yield m


@pytest.fixture
def mock_news_empty():
    with patch("stocksense.orchestration.react_flow.get_news", return_value=[]) as m:
        yield m


@pytest.fixture
def mock_news_error():
    with patch(
        "stocksense.orchestration.react_flow.get_news",
        side_effect=DataCollectionError("NewsAPI timeout"),
    ) as m:
        yield m


@pytest.fixture
def mock_price_none():
    with patch("stocksense.orchestration.react_flow.get_price_history", return_value=None) as m:
        yield m


# ── News Headlines Tests ───────────────────────────────────────────────────────


class TestNewsHeadlines:

    def test_fetch_news_headlines_success(self, mock_news):
        result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        assert result["success"] is True
        assert result["ticker"] == "AAPL"
        assert result["headlines"] == FAKE_HEADLINES
        assert result["count"] == 3

    def test_fetch_news_headlines_structure(self, mock_news):
        result = fetch_news_headlines.invoke({"ticker": "MSFT"})
        for key in ["success", "headlines", "ticker", "count"]:
            assert key in result
        assert isinstance(result["headlines"], list)
        assert all(isinstance(h, str) for h in result["headlines"])

    def test_fetch_news_headlines_ticker_normalized_to_uppercase(self, mock_news):
        result = fetch_news_headlines.invoke({"ticker": "aapl"})
        assert result["ticker"] == "AAPL"

    def test_fetch_news_headlines_empty_returns_success_false(self, mock_news_empty):
        result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        assert result["success"] is False
        assert result["headlines"] == []

    def test_fetch_news_headlines_data_collection_error(self, mock_news_error):
        result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        assert result["success"] is False
        assert "NewsAPI timeout" in result.get("error", "")
        assert result["headlines"] == []


# ── Price Data Tests ───────────────────────────────────────────────────────────


class TestPriceData:

    def test_fetch_price_data_success(self, mock_price):
        result = fetch_price_data.invoke({"ticker": "GOOGL"})
        assert isinstance(result, dict)
        assert "price_data" in result
        assert result["ticker"] == "GOOGL"

    def test_fetch_price_data_structure(self, mock_price):
        result = fetch_price_data.invoke({"ticker": "AAPL", "period": "5d"})
        for key in ["success", "price_data", "ticker", "has_data"]:
            assert key in result
        if result["price_data"]:
            record = result["price_data"][0]
            for field in ["Date", "Open", "High", "Low", "Close", "Volume"]:
                assert field in record

    def test_fetch_price_data_ticker_normalized(self, mock_price):
        result = fetch_price_data.invoke({"ticker": "tsla"})
        assert result["ticker"] == "TSLA"

    def test_fetch_price_data_none_returns_empty(self, mock_price_none):
        result = fetch_price_data.invoke({"ticker": "AAPL"})
        assert isinstance(result["price_data"], list)
        assert result["price_data"] == []


# ── Combined Tests ─────────────────────────────────────────────────────────────


class TestCombinedDataRetrieval:

    def test_fetch_data_consistency(self, mock_news, mock_price):
        ticker = "msft"
        news_result = fetch_news_headlines.invoke({"ticker": ticker})
        price_result = fetch_price_data.invoke({"ticker": ticker})
        assert news_result["ticker"].upper() == ticker.upper()
        assert price_result["ticker"].upper() == ticker.upper()

    def test_error_handling_consistency(self, mock_news_error, mock_price_none):
        news_result = fetch_news_headlines.invoke({"ticker": "AAPL"})
        price_result = fetch_price_data.invoke({"ticker": "AAPL"})
        assert isinstance(news_result, dict)
        assert isinstance(price_result, dict)
        assert "headlines" in news_result
        assert "price_data" in price_result


# ── Parametrized coverage ──────────────────────────────────────────────────────


@pytest.mark.parametrize("ticker", ["AAPL", "MSFT", "GOOGL"])
def test_multiple_valid_tickers(ticker, mock_news, mock_price):
    news_result = fetch_news_headlines.invoke({"ticker": ticker})
    price_result = fetch_price_data.invoke({"ticker": ticker})
    assert news_result["ticker"] == ticker
    assert price_result["ticker"] == ticker
    assert news_result["success"] is True
