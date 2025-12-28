"""
StockSense Core Package

Data collection, validation, configuration utilities, and schemas.
"""
from .data_collectors import get_news, get_price_history, get_fundamental_data
from .analyzer import analyze_sentiment_of_headlines, analyze_sentiment_structured
from .validation import validate_ticker
from .config import get_chat_llm, get_newsapi_key, ConfigurationError
from .schemas import (
    HeadlineSentiment,
    SentimentAnalysisResult,
    KeyTheme,
)

__all__ = [
    "get_news",
    "get_price_history", 
    "get_fundamental_data",
    "analyze_sentiment_of_headlines",
    "analyze_sentiment_structured",
    "validate_ticker",
    "get_chat_llm",
    "get_newsapi_key",
    "ConfigurationError",
    "HeadlineSentiment",
    "SentimentAnalysisResult",
    "KeyTheme",
]
