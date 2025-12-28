"""
Pytest configuration and shared fixtures for StockSense tests.
"""

import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return the project root path."""
    return project_root


@pytest.fixture
def valid_tickers():
    """Fixture providing list of valid test tickers."""
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]


@pytest.fixture
def invalid_tickers():
    """Fixture providing list of invalid test tickers."""
    return ["INVALIDXYZ", "NOTREAL123", "BADTICKER"]


@pytest.fixture
def sample_analysis_result():
    """Fixture providing a sample analysis result structure."""
    return {
        "ticker": "AAPL",
        "summary": "Test analysis summary.",
        "sentiment_report": "Overall Sentiment: Bullish",
        "headlines": ["Headline 1", "Headline 2"],
        "price_data": [
            {"Date": "2024-01-01", "Open": 100, "High": 105, "Low": 99, "Close": 104, "Volume": 1000000}
        ],
        "reasoning_steps": ["Step 1", "Step 2"],
        "tools_used": ["fetch_news_headlines", "fetch_price_data"],
        "iterations": 3,
        "overall_sentiment": "Bullish",
        "overall_confidence": 0.85,
    }
