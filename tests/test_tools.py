#!/usr/bin/env python3
"""
Unit Tests for StockSense Agent Tools

This module contains unit tests for the core data collection tools
used by the StockSense ReAct Agent.

Test Coverage:
- fetch_news_headlines tool
- fetch_price_data tool  
- Error handling for invalid tickers
"""

import pytest
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from stocksense.react_agent import fetch_news_headlines, fetch_price_data


class TestNewsHeadlines:
    """Test cases for the fetch_news_headlines tool"""
    
    def test_fetch_news_headlines_success(self):
        """Test successful news headlines retrieval with valid ticker"""
        # Use a common, stable ticker for testing
        ticker = "MSFT"
        
        # Call the tool function
        result = fetch_news_headlines.invoke({"ticker": ticker})
        
        # Assertions
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "headlines" in result, "Result should contain 'headlines' key"
        assert isinstance(result["headlines"], list), "Headlines should be a list"
        
        # Check for successful retrieval
        if result.get("success", False):
            assert len(result["headlines"]) > 0, "Headlines list should not be empty for valid ticker"
        
        # Verify expected structure
        assert "ticker" in result, "Result should contain ticker information"
        assert result["ticker"] == ticker.upper(), "Ticker should be normalized to uppercase"
    
    def test_fetch_news_headlines_structure(self):
        """Test the structure of news headlines response"""
        ticker = "AAPL"
        result = fetch_news_headlines.invoke({"ticker": ticker})
        
        # Check response structure
        expected_keys = ["success", "headlines", "ticker"]
        for key in expected_keys:
            assert key in result, f"Result should contain '{key}' key"
        
        # If successful, check headlines structure
        if result.get("success") and result.get("headlines"):
            headlines = result["headlines"]
            assert all(isinstance(headline, str) for headline in headlines), \
                "All headlines should be strings"
    
    def test_fetch_news_headlines_invalid_ticker(self):
        """Test news headlines tool with invalid ticker"""
        invalid_ticker = "INVALIDTICKERXYZ"
        
        # Call the tool function
        result = fetch_news_headlines.invoke({"ticker": invalid_ticker})
        
        # Assertions for graceful error handling
        assert isinstance(result, dict), "Result should be a dictionary even for invalid ticker"
        assert "headlines" in result, "Result should contain 'headlines' key"
        assert isinstance(result["headlines"], list), "Headlines should be a list"
        
        # Should handle gracefully - either empty list or error indicator
        assert (
            len(result["headlines"]) == 0 or 
            result.get("success") == False or
            any("error" in str(result).lower() for key in result.keys())
        ), "Invalid ticker should be handled gracefully"


class TestPriceData:
    """Test cases for the fetch_price_data tool"""
    
    def test_fetch_price_data_success(self):
        """Test successful price data retrieval with valid ticker"""
        ticker = "GOOGL"
        
        # Call the tool function
        result = fetch_price_data.invoke({"ticker": ticker})
        
        # Assertions
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "price_data" in result, "Result should contain 'price_data' key"
        assert isinstance(result["price_data"], list), "Price data should be a list"
        
        # Check for successful retrieval
        if result.get("success", False):
            assert len(result["price_data"]) > 0, "Price data list should not be empty for valid ticker"
            
            # Verify OHLCV structure if data is present
            if result["price_data"]:
                sample_record = result["price_data"][0]
                assert isinstance(sample_record, dict), "Each price record should be a dictionary"
                
                # Check for required OHLCV fields
                expected_fields = ["Date", "Open", "High", "Low", "Close", "Volume"]
                for field in expected_fields:
                    assert field in sample_record, f"Price record should contain '{field}' field"
        
        # Verify expected metadata
        assert "ticker" in result, "Result should contain ticker information"
        assert result["ticker"] == ticker.upper(), "Ticker should be normalized to uppercase"
    
    def test_fetch_price_data_structure(self):
        """Test the structure of price data response"""
        ticker = "AAPL"
        result = fetch_price_data.invoke({"ticker": ticker, "period": "5d"})
        
        # Check response structure
        expected_keys = ["success", "price_data", "ticker", "has_data"]
        for key in expected_keys:
            assert key in result, f"Result should contain '{key}' key"
        
        # If successful, validate data structure
        if result.get("success") and result.get("price_data"):
            price_data = result["price_data"]
            
            for record in price_data[:3]:  # Check first 3 records
                assert isinstance(record, dict), "Each price record should be a dictionary"
                
                # Validate data types
                if "Date" in record:
                    assert isinstance(record["Date"], str), "Date should be a string"
                
                numeric_fields = ["Open", "High", "Low", "Close"]
                for field in numeric_fields:
                    if field in record and record[field] is not None:
                        assert isinstance(record[field], (int, float)), \
                            f"{field} should be numeric"
                
                if "Volume" in record and record["Volume"] is not None:
                    assert isinstance(record["Volume"], (int, float)), \
                        "Volume should be numeric"
    
    def test_fetch_price_data_invalid_ticker(self):
        """Test price data tool with invalid ticker"""
        invalid_ticker = "INVALIDTICKERXYZ"
        
        # Call the tool function
        result = fetch_price_data.invoke({"ticker": invalid_ticker})
        
        # Assertions for graceful error handling
        assert isinstance(result, dict), "Result should be a dictionary even for invalid ticker"
        assert "price_data" in result, "Result should contain 'price_data' key"
        assert isinstance(result["price_data"], list), "Price data should be a list"
        
        # Should handle gracefully - either empty list or error indicator
        assert (
            len(result["price_data"]) == 0 or 
            result.get("success") == False or
            "error" in str(result).lower()
        ), "Invalid ticker should be handled gracefully"


class TestCombinedDataRetrieval:
    """Test cases for combined data retrieval scenarios"""
    
    def test_fetch_data_consistency(self):
        """Test that both tools return consistent ticker formatting"""
        ticker = "msft"  # Use lowercase to test normalization
        
        news_result = fetch_news_headlines.invoke({"ticker": ticker})
        price_result = fetch_price_data.invoke({"ticker": ticker})
        
        # Both should return the ticker (case-insensitive comparison)
        assert news_result.get("ticker").upper() == ticker.upper()
        assert price_result.get("ticker").upper() == ticker.upper()
    
    def test_error_handling_consistency(self):
        """Test that both tools handle errors consistently"""
        invalid_ticker = "INVALIDTICKER123"
        
        news_result = fetch_news_headlines.invoke({"ticker": invalid_ticker})
        price_result = fetch_price_data.invoke({"ticker": invalid_ticker})
        
        # Both should return dictionary structure even on error
        assert isinstance(news_result, dict)
        assert isinstance(price_result, dict)
        
        # Both should have expected keys
        assert "headlines" in news_result
        assert "price_data" in price_result


# Pytest fixtures for common test data
@pytest.fixture
def valid_tickers():
    """Fixture providing list of valid test tickers"""
    return ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]


@pytest.fixture
def invalid_tickers():
    """Fixture providing list of invalid test tickers"""
    return ["INVALIDXYZ", "NOTREAL123", "BADTICKER"]


# Integration test using fixtures
def test_multiple_valid_tickers(valid_tickers):
    """Test tools with multiple valid tickers"""
    for ticker in valid_tickers[:2]:  # Test first 2 to avoid rate limits
        news_result = fetch_news_headlines.invoke({"ticker": ticker})
        price_result = fetch_price_data.invoke({"ticker": ticker})
        
        # Basic structure checks
        assert isinstance(news_result, dict)
        assert isinstance(price_result, dict)
        assert news_result.get("ticker") == ticker
        assert price_result.get("ticker") == ticker


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v"])
