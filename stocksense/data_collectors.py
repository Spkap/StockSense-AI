import os
from typing import List, Optional
from datetime import datetime, timedelta
import yfinance as yf
from newsapi import NewsApiClient
from .config import get_newsapi_key, ConfigurationError


def get_news(ticker: str, days: int = 7) -> List[str]:
    """Fetch recent news headlines related to a stock ticker."""
    try:
        api_key = get_newsapi_key()
        newsapi = NewsApiClient(api_key=api_key)

        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')

        articles = newsapi.get_everything(
            q=ticker,
            language='en',
            sort_by='publishedAt',
            from_param=from_date_str,
            to=to_date_str,
            page_size=20
        )

        if articles['status'] == 'ok':
            headlines = []
            for article in articles['articles']:
                if article['title'] and article['title'] != '[Removed]':
                    headlines.append(article['title'])
            return headlines
        else:
            return []

    except ConfigurationError as e:
        return []
    except Exception as e:
        return []


def get_price_history(ticker: str, period: str = "1mo") -> Optional[object]:
    """Fetch historical price data for a stock ticker."""
    try:
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)

        if history.empty:
            return None

        return history

    except Exception as e:
        return None


if __name__ == '__main__':
    test_ticker = "AAPL"
    headlines = get_news(test_ticker, days=7)
    price_data = get_price_history(test_ticker, period="1mo")