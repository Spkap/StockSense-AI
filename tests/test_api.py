#!/usr/bin/env python3
"""
Integration Tests for StockSense Agent API

This module contains integration tests for the FastAPI endpoints
of the StockSense ReAct Agent application.

Test Coverage:
- Health check endpoint
- Cached tickers endpoint
- API response format validation
- Error handling
"""

import pytest
import requests
import time
import sys
from pathlib import Path

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configuration
BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 10  # seconds


class TestAPIHealthAndStatus:
    """Test cases for basic API health and status endpoints"""
    
    def test_health_check(self):
        """Test the health check endpoint"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
            
            # Assert response status
            assert response.status_code == 200, f"Health check should return 200, got {response.status_code}"
            
            # Assert response content - enhanced health check format
            response_json = response.json()
            assert response_json.get("status") in ["ok", "degraded"], \
                f"Health check status should be 'ok' or 'degraded', got {response_json.get('status')}"
            assert "timestamp" in response_json, "Health check should include timestamp"
            assert "version" in response_json, "Health check should include version"
            assert "checks" in response_json, "Health check should include checks dict"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running. Start with: python -m stocksense.main")
        except requests.exceptions.Timeout:
            pytest.fail("Health check endpoint timed out")
    
    def test_health_check_response_time(self):
        """Test that health check responds quickly"""
        try:
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
            response_time = time.time() - start_time
            
            assert response.status_code == 200
            assert response_time < 2.0, f"Health check should respond quickly, took {response_time:.2f}s"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_root_endpoint(self):
        """Test the root endpoint returns welcome message"""
        try:
            response = requests.get(f"{BASE_URL}/", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 200
            response_json = response.json()
            
            # Check for expected fields
            assert "message" in response_json
            assert "description" in response_json
            assert "docs" in response_json
            assert "health" in response_json
            
            # Verify content
            assert "StockSense ReAct Agent API" in response_json["message"]
            assert response_json["docs"] == "/docs"
            assert response_json["health"] == "/health"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestCachedTickersEndpoint:
    """Test cases for the cached tickers endpoint"""
    
    def test_cached_tickers_endpoint(self):
        """Test the cached tickers endpoint basic functionality"""
        try:
            response = requests.get(f"{BASE_URL}/cached-tickers", timeout=REQUEST_TIMEOUT)
            
            # Assert response status
            assert response.status_code == 200, \
                f"Cached tickers endpoint should return 200, got {response.status_code}"
            
            # Assert response structure
            response_json = response.json()
            assert isinstance(response_json, dict), "Response should be a dictionary"
            assert "tickers" in response_json, "Response should contain 'tickers' key"
            assert isinstance(response_json["tickers"], list), \
                "The 'tickers' value should be a list"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
        except requests.exceptions.Timeout:
            pytest.fail("Cached tickers endpoint timed out")
    
    def test_cached_tickers_response_structure(self):
        """Test the structure of cached tickers response"""
        try:
            response = requests.get(f"{BASE_URL}/cached-tickers", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 200
            response_json = response.json()
            
            # Check for expected keys
            expected_keys = ["message", "count", "tickers"]
            for key in expected_keys:
                assert key in response_json, f"Response should contain '{key}' key"
            
            # Validate data types
            assert isinstance(response_json["message"], str)
            assert isinstance(response_json["count"], int)
            assert isinstance(response_json["tickers"], list)
            
            # Validate consistency
            assert response_json["count"] == len(response_json["tickers"]), \
                "Count should match the number of tickers in the list"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_cached_tickers_empty_cache(self):
        """Test cached tickers endpoint when cache is empty"""
        try:
            response = requests.get(f"{BASE_URL}/cached-tickers", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 200
            response_json = response.json()
            
            # Should handle empty cache gracefully
            assert "tickers" in response_json
            assert isinstance(response_json["tickers"], list)
            assert response_json["count"] >= 0
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestAPIErrorHandling:
    """Test cases for API error handling"""
    
    def test_nonexistent_endpoint(self):
        """Test that non-existent endpoints return 404"""
        try:
            response = requests.get(f"{BASE_URL}/nonexistent-endpoint", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 404, \
                f"Non-existent endpoint should return 404, got {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_invalid_method(self):
        """Test that invalid HTTP methods are handled properly"""
        try:
            # Try DELETE on health endpoint (should not be allowed)
            response = requests.delete(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
            
            # Should return 405 Method Not Allowed or 422 Unprocessable Entity
            assert response.status_code in [405, 422], \
                f"Invalid method should return 405 or 422, got {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestAPIDocumentation:
    """Test cases for API documentation endpoints"""
    
    def test_docs_endpoint_accessible(self):
        """Test that the API docs endpoint is accessible"""
        try:
            response = requests.get(f"{BASE_URL}/docs", timeout=REQUEST_TIMEOUT)
            
            # Should return 200 and HTML content
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "").lower()
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
    
    def test_redoc_endpoint_accessible(self):
        """Test that the ReDoc endpoint is accessible"""
        try:
            response = requests.get(f"{BASE_URL}/redoc", timeout=REQUEST_TIMEOUT)
            
            # Should return 200 and HTML content
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "").lower()
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


class TestAPIPerformance:
    """Test cases for API performance and reliability"""
    
    def test_concurrent_health_checks(self):
        """Test multiple concurrent health check requests"""
        try:
            import concurrent.futures
            import threading
            
            def make_health_request():
                response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
                return response.status_code
            
            # Make 5 concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_health_request) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # All should succeed
            assert all(status == 200 for status in results), \
                f"All concurrent requests should succeed, got {results}"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")
        except ImportError:
            pytest.skip("concurrent.futures not available")
    
    def test_api_response_headers(self):
        """Test that API returns appropriate headers"""
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=REQUEST_TIMEOUT)
            
            assert response.status_code == 200
            
            # Check for standard HTTP headers
            headers = response.headers
            assert "content-type" in headers, "Content-Type header should be present"
            assert "server" in headers, "Server header should be present"
            
            # CORS headers are optional but good to have
            has_cors = ("access-control-allow-origin" in headers or 
                       "Access-Control-Allow-Origin" in headers)
            # Log CORS status but don't fail the test
            print(f"CORS headers present: {has_cors}")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API server is not running")


# Utility fixtures and helper functions
@pytest.fixture(scope="session")
def api_server_check():
    """Fixture to check if API server is running before tests"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            pytest.exit("API server is not responding correctly")
    except requests.exceptions.ConnectionError:
        pytest.exit("API server is not running. Start with: python -m stocksense.main")
    return True


@pytest.fixture
def api_client():
    """Fixture providing a configured requests session"""
    session = requests.Session()
    session.timeout = REQUEST_TIMEOUT
    return session


# Integration test using fixtures
def test_api_integration_flow(api_client):
    """Test a complete integration flow"""
    try:
        # 1. Check health
        health_response = api_client.get(f"{BASE_URL}/health")
        assert health_response.status_code == 200
        
        # 2. Get root info
        root_response = api_client.get(f"{BASE_URL}/")
        assert root_response.status_code == 200
        
        # 3. Check cached tickers
        tickers_response = api_client.get(f"{BASE_URL}/cached-tickers")
        assert tickers_response.status_code == 200
        
        # All responses should be JSON
        assert all(resp.headers.get("content-type", "").startswith("application/json") 
                  for resp in [health_response, root_response, tickers_response])
        
    except requests.exceptions.ConnectionError:
        pytest.skip("API server is not running")


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    print(f"Testing API at: {BASE_URL}")
    print("Make sure the API server is running with: python -m stocksense.main")
    pytest.main([__file__, "-v"])
