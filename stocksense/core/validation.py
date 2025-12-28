"""
Ticker validation utilities for StockSense.
"""
import re
import logging
from typing import Tuple, Optional

import yfinance as yf

logger = logging.getLogger("stocksense.validation")


# Regex pattern for valid ticker format (1-5 uppercase letters)
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}$')


def validate_ticker_format(ticker: str) -> Tuple[bool, Optional[str]]:
    """
    Validate ticker format without network call.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ticker:
        return False, "Ticker cannot be empty"
    
    ticker = ticker.upper().strip()
    
    if len(ticker) > 5:
        return False, f"Ticker '{ticker}' is too long (max 5 characters)"
    
    if len(ticker) < 1:
        return False, "Ticker cannot be empty"
    
    if not TICKER_PATTERN.match(ticker):
        return False, f"Ticker '{ticker}' contains invalid characters (only A-Z allowed)"
    
    return True, None


def validate_ticker_exists(ticker: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a ticker exists and has market data.
    Uses yfinance for validation (fast, no API key required).
    
    Args:
        ticker: Stock ticker symbol (should be pre-validated for format)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ticker = ticker.upper().strip()
        stock = yf.Ticker(ticker)
        
        # Try to get basic info - this is fast and doesn't require full data fetch
        info = stock.info
        
        # Check if we got meaningful data back
        # yfinance returns empty dict or minimal data for invalid tickers
        if not info:
            return False, f"Ticker '{ticker}' not found"
        
        # Check for common indicators that ticker is valid
        # regularMarketPrice being None often indicates invalid/delisted ticker
        if info.get('regularMarketPrice') is None and info.get('previousClose') is None:
            # Could be a valid ETF or mutual fund, check for other indicators
            if info.get('shortName') is None and info.get('longName') is None:
                return False, f"Ticker '{ticker}' not found or has no market data"
        
        return True, None
        
    except Exception as e:
        logger.warning(f"Error validating ticker {ticker}: {e}")
        # Don't block on validation errors - let the analysis try anyway
        return True, None


def validate_ticker(ticker: str, check_exists: bool = True) -> Tuple[bool, Optional[str]]:
    """
    Full ticker validation: format + existence check.
    
    Args:
        ticker: Stock ticker symbol
        check_exists: Whether to verify ticker exists via yfinance
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    # First check format
    is_valid, error = validate_ticker_format(ticker)
    if not is_valid:
        return is_valid, error
    
    # Then check existence if requested
    if check_exists:
        is_valid, error = validate_ticker_exists(ticker)
        if not is_valid:
            return is_valid, error
    
    return True, None
