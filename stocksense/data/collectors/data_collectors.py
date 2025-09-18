import os
import sys
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import yfinance as yf
from newsapi import NewsApiClient

# Add the parent directories to Python path to find core module
current_dir = os.path.dirname(os.path.abspath(__file__))
collectors_dir = os.path.dirname(current_dir)
stocksense_dir = os.path.dirname(collectors_dir)
sys.path.append(stocksense_dir)

from core.config import get_newsapi_key, ConfigurationError



def get_news(ticker: str, days: int = 7) -> List[Dict[str, str]]:
    """Fetch recent news headlines and URLs related to a stock ticker.
    
    Returns:
        List of dictionaries with 'headline' and 'url'
    """
    try:
        api_key = get_newsapi_key()
        newsapi = NewsApiClient(api_key=api_key)

        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)

        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')

        try:
            results = newsapi.get_everything(
                q=ticker ,
                language='en',
                sort_by='publishedAt',
                from_param=from_date_str,
                to=to_date_str,
                page_size=5

            )
            
            news_data = []
            if results and results.get('status') == 'ok':
                articles = results.get('articles', [])
                
                for article in articles:
                    if article.get('title') and article.get('url'):
                        news_data.append({
                            'headline': article['title'],
                            'url': article['url'],
                        })
            
            return news_data
            
        except Exception as e:
            print(f"Error fetching news for {ticker}: {str(e)}")
            return []
        
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        return []
    except Exception as e:
        print(f"Unexpected error in get_news: {str(e)}")
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


