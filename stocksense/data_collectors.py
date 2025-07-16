"""
Data collection module for StockSense ReAct Agent.

This module provides functions to collect stock-related news and price data
from various sources including NewsAPI and Yahoo Finance for the ReAct Agent.
"""

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
        
        print(f"Fetching news for {ticker} from {from_date_str} to {to_date_str}")
        
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
            
            print(f"Successfully fetched {len(headlines)} headlines for {ticker}")
            return headlines
        else:
            print(f"Error from NewsAPI: {articles.get('message', 'Unknown error')}")
            return []
            
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        return []
    except Exception as e:
        print(f"Error fetching news for {ticker}: {str(e)}")
        return []


def get_price_history(ticker: str, period: str = "1mo") -> Optional[object]:
    """Fetch historical price data for a stock ticker."""
    try:
        print(f"Fetching price history for {ticker} (period: {period})")
        
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)
        
        if history.empty:
            print(f"Warning: No price data found for ticker {ticker}")
            return None
        
        print(f"Successfully fetched {len(history)} days of price data for {ticker}")
        return history
        
    except Exception as e:
        print(f"Error fetching price history for {ticker}: {str(e)}")
        return None


if __name__ == '__main__':
    print("Testing StockSense ReAct Agent Data Collectors")
    print("=" * 50)
    
    test_ticker = "AAPL"
    
    print(f"\n1. Testing news collection for {test_ticker}:")
    headlines = get_news(test_ticker, days=7)
    
    if headlines:
        print(f"\nFound {len(headlines)} headlines:")
        for i, headline in enumerate(headlines[:5], 1):
            print(f"{i}. {headline}")
        if len(headlines) > 5:
            print(f"... and {len(headlines) - 5} more headlines")
    else:
        print("No headlines found or error occurred")
    
    print(f"\n\n2. Testing price history collection for {test_ticker}:")
    price_data = get_price_history(test_ticker, period="1mo")
    
    if price_data is not None:
        print(f"\nPrice data shape: {price_data.shape}")
        print(f"Date range: {price_data.index[0].date()} to {price_data.index[-1].date()}")
        print(f"\nLatest prices:")
        print(f"Open: ${price_data['Open'].iloc[-1]:.2f}")
        print(f"High: ${price_data['High'].iloc[-1]:.2f}")
        print(f"Low: ${price_data['Low'].iloc[-1]:.2f}")
        print(f"Close: ${price_data['Close'].iloc[-1]:.2f}")
        print(f"Volume: {price_data['Volume'].iloc[-1]:,}")
        
        print(f"\nFirst few rows of data:")
        print(price_data.head(3).round(2))
    else:
        print("No price data found or error occurred")
    
    print("Testing completed!")
