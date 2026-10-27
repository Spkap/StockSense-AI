import logging
import math
import os
import random
import time
from numbers import Integral, Real
from urllib.parse import urlparse
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import yfinance as yf
import pandas as pd
from newsapi import NewsApiClient
from newsapi.const import EVERYTHING_URL
from requests.exceptions import ConnectionError as RequestsConnectionError, HTTPError, Timeout as RequestsTimeout
from .config import get_newsapi_key, ConfigurationError

logger = logging.getLogger("stocksense.data_collectors")


class ProviderError(Exception):
    """A safe, actionable upstream failure; never include credentials or raw responses."""
    def __init__(self, message: str, code: str, retryable: bool = False):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class NewsHeadlines(list):
    """List-compatible headlines with their original source records."""
    def __init__(self, articles):
        super().__init__(article['title'] for article in articles)
        self.articles = articles


def _retry_provider(operation, attempts=2):
    for attempt in range(attempts):
        try:
            return operation()
        except ProviderError as exc:
            if not exc.retryable or attempt + 1 == attempts:
                raise
            time.sleep(0.5 * (2 ** attempt) + random.uniform(0, 0.2))


def _safe_article_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    try:
        parsed = urlparse(value)
        return value if parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password else None
    except ValueError:
        return None


def attach_news_sources(analyses, articles):
    """Attach only matching provider records; never infer a source by position."""
    sources = {article['title'].strip().casefold(): article for article in articles if article.get('title')}
    return [{**item, **({'source': source.get('source'), 'url': source.get('url'),
                        'published_at': source.get('published_at')}
                       if (source := sources.get(str(item.get('headline', '')).strip().casefold())) else {})}
            for item in analyses]


def json_safe_data(value):
    """Represent unavailable numeric market values as JSON null, never NaN/Infinity."""
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, Real):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: json_safe_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe_data(item) for item in value]
    return value


def get_news(ticker: str, days: int = 7) -> List[str]:
    """Fetch recent news headlines related to a stock ticker."""
    try:
        api_key = get_newsapi_key()
        newsapi = NewsApiClient(api_key=api_key)

        to_date = datetime.now(timezone.utc)
        from_date = to_date - timedelta(days=days)

        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')

        # The installed client predates searchIn; use its authenticated session
        # against the documented endpoint so body-only mentions do not swamp results.
        def fetch():
            try:
                response = newsapi.request_method.get(
                    EVERYTHING_URL, auth=newsapi.auth, timeout=15,
                    params={"q": ticker, "searchIn": "title,description", "language": "en",
                            "sortBy": "publishedAt", "from": from_date_str, "to": to_date_str,
                            "pageSize": 20},
                )
                response.raise_for_status()
                payload = response.json()
            except HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else response.status_code
                try:
                    code = response.json().get('code', '')
                except Exception:
                    code = ''
                if status in (401, 403) or code in ('apiKeyDisabled', 'apiKeyInvalid', 'apiKeyMissing'):
                    raise ProviderError('News service rejected its credentials or plan.', 'news_auth') from exc
                if status == 429 or code in ('apiKeyExhausted', 'rateLimited'):
                    raise ProviderError('News service is rate limited or its quota is exhausted. Try again later.', 'news_rate_limit') from exc
                if status == 400:
                    raise ProviderError('News service rejected the search request. Check the ticker and retry.', 'news_request') from exc
                raise ProviderError('News service is temporarily unavailable. Please retry.', 'news_unavailable', status >= 500) from exc
            except (RequestsTimeout, RequestsConnectionError) as exc:
                raise ProviderError('News service connection failed. Please retry.', 'news_connection', True) from exc
            except ValueError as exc:
                raise ProviderError('News service returned an unreadable response. Please retry.', 'news_response', True) from exc
            if isinstance(payload, dict) and payload.get('status') == 'error':
                code = payload.get('code', '')
                if code in ('apiKeyDisabled', 'apiKeyInvalid', 'apiKeyMissing'):
                    raise ProviderError('News service rejected its credentials or plan.', 'news_auth')
                if code in ('apiKeyExhausted', 'rateLimited'):
                    raise ProviderError('News service is rate limited or its quota is exhausted. Try again later.', 'news_rate_limit')
                raise ProviderError('News service is temporarily unavailable. Please retry.', 'news_unavailable', code == 'unexpectedError')
            if not isinstance(payload, dict) or payload.get('status') != 'ok' or not isinstance(payload.get('articles'), list):
                raise ProviderError('News service returned an incomplete response. Please retry.', 'news_response', True)
            return payload['articles']

        articles = _retry_provider(fetch)
        if articles is not None:
            records = []
            seen = set()
            for article in articles:
                if not isinstance(article, dict):
                    continue
                title = article.get('title')
                if not isinstance(title, str):
                    continue
                title = title.strip()
                normalized = title.casefold()
                if title and normalized != '[removed]' and normalized not in seen:
                    source = article.get('source')
                    source_name = source.get('name') if isinstance(source, dict) else None
                    records.append({'title': title, 'source': source_name if isinstance(source_name, str) else None,
                                    'url': _safe_article_url(article.get('url')),
                                    'published_at': article.get('publishedAt') if isinstance(article.get('publishedAt'), str) else None})
                    seen.add(normalized)
            return NewsHeadlines(records)

    except ConfigurationError as e:
        raise ProviderError('News service is not configured.', 'news_config') from e
    except ProviderError:
        raise
    except Exception as e:
        logger.warning('News collection failed for %s (%s)', ticker, type(e).__name__)
        raise ProviderError('News service is temporarily unavailable. Please retry.', 'news_unavailable') from e


def _yahoo_call(operation):
    def fetch():
        try:
            return operation()
        except Exception as exc:
            name = type(exc).__name__.lower()
            status = getattr(getattr(exc, 'response', None), 'status_code', None) or getattr(exc, 'status_code', None)
            if status == 429:
                raise ProviderError('Market data is rate limited. Please retry shortly.', 'market_rate_limit', True) from exc
            if status in (408, 500, 502, 503, 504):
                raise ProviderError('Market data is temporarily unavailable. Please retry.', 'market_unavailable', True) from exc
            if 'ratelimit' in name:
                raise ProviderError('Market data is rate limited. Please retry shortly.', 'market_rate_limit', True) from exc
            if 'timeout' in name or 'connection' in name:
                raise ProviderError('Market data connection failed. Please retry.', 'market_connection', True) from exc
            if 'missing' in name:
                raise ProviderError('No market data was returned. Check the ticker or try again.', 'market_no_data') from exc
            if 'invalidperiod' in name:
                raise ProviderError('Price history is unavailable for the selected period. Please try again.', 'market_period') from exc
            raise ProviderError('Market data is temporarily unavailable. Please retry.', 'market_unavailable') from exc
    return _retry_provider(fetch)


def get_price_history(ticker: str, period: str = "1mo") -> Optional[object]:
    """Fetch historical price data for a stock ticker."""
    try:
        stock = yf.Ticker(ticker)
        history = _yahoo_call(lambda: stock.history(period=period, interval="1d", auto_adjust=True, timeout=12, raise_errors=True))

        if history.empty:
            return None

        return history

    except ProviderError:
        raise
    except Exception as e:
        logger.warning('Price collection failed for %s (%s)', ticker, type(e).__name__)
        raise ProviderError('Market data is temporarily unavailable. Please retry.', 'market_unavailable') from e


def get_fundamental_data(ticker: str) -> Optional[dict]:
    """
    Fetch fundamental financial data (Income Statement, Balance Sheet, Cash Flow) 
    and key statistics.
    """
    try:
        stock = yf.Ticker(ticker)
        
        # Helper to convert DataFrame to dict safely
        def safe_to_dict(df):
            if df is None or df.empty:
                return {}
            # Convert timestamp keys to strings
            return {k.strftime('%Y-%m-%d') if isinstance(k, datetime) else str(k): v 
                    for k, v in df.to_dict().items()}

        missing = []
        market_throttled = False
        def component(name, getter, default):
            nonlocal market_throttled
            if market_throttled:
                missing.append(name)
                return default
            try:
                value = _yahoo_call(getter)
                if value is None or getattr(value, 'empty', False) or (isinstance(value, dict) and not value):
                    missing.append(name)
                    return default
                return value
            except ProviderError as exc:
                missing.append(name)
                if exc.code == 'market_rate_limit':
                    market_throttled = True
                logger.warning('Fundamentals %s unavailable for %s (%s)', name, ticker, exc.code)
                return default

        info = component('company information', lambda: stock.info, {})
        if not isinstance(info, dict):
            info = {}
            missing.append('company information')
        income_stmt = component('income statement', lambda: stock.income_stmt, None)
        balance_sheet = component('balance sheet', lambda: stock.balance_sheet, None)
        cash_flow = component('cash flow', lambda: stock.cashflow, None)
        
        result = {
            "info": {
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency"),
                "company_name": info.get("shortName") or info.get("longName"),
                "exchange": info.get("exchange"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "peg_ratio": info.get("pegRatio"),
                "price_to_book": info.get("priceToBook"),
                "profit_margins": info.get("profitMargins"),
                "revenue_growth": info.get("revenueGrowth"),
                "debt_to_equity": info.get("debtToEquity"),
                "free_cashflow": info.get("freeCashflow"),
                "target_high": info.get("targetHighPrice"),
                "target_low": info.get("targetLowPrice"),
                "recommendation_mean": info.get("recommendationMean"), # 1 is Strong Buy, 5 is Sell
            },
            "income_statement": safe_to_dict(income_stmt),
            "balance_sheet": safe_to_dict(balance_sheet),
            "cash_flow": safe_to_dict(cash_flow)
        }
        if missing:
            result['unavailable_sections'] = missing
        if not any(v is not None for v in result['info'].values()) and not any(result[k] for k in ('income_statement', 'balance_sheet', 'cash_flow')):
            return None
        return json_safe_data(result)
    except Exception as e:
        logger.error(f"Error fetching fundamentals for {ticker}: {e}")
        return None


if __name__ == '__main__':
    test_ticker = "AAPL"
    headlines = get_news(test_ticker, days=7)
    price_data = get_price_history(test_ticker, period="1mo")
