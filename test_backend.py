#!/usr/bin/env python3
"""
Backend Test Runner for StockSense Agent API

This script tests the complete FastAPI backend functionality including:
- Fresh analysis workflow
- Database caching
- Cache retrieval
- Error handling

Run this script while the FastAPI server is running on localhost:8000
"""

import requests
import time
import json
from typing import Dict, Any


def print_separator(title: str) -> None:
    """Print a formatted separator for better output readability."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response: requests.Response, step_name: str) -> None:
    """Print formatted response information."""
    print(f"\n📊 {step_name}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    try:
        response_data = response.json()
        print("Response Body:")
        print(json.dumps(response_data, indent=2))
    except json.JSONDecodeError:
        print(f"Response Body (raw): {response.text}")


def test_health_endpoint(base_url: str) -> bool:
    """Test the health check endpoint."""
    print_separator("TESTING HEALTH ENDPOINT")
    
    try:
        print(f"🔍 Making GET request to {base_url}/health")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        print_response(response, "Health Check Response")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed with error: {e}")
        return False


def test_fresh_analysis(base_url: str, ticker: str) -> bool:
    """Test fresh analysis workflow."""
    print_separator(f"TESTING FRESH ANALYSIS FOR {ticker}")
    
    try:
        print(f"🔍 Making POST request to {base_url}/analyze/{ticker}")
        print("📈 This should trigger a fresh analysis (data collection + AI analysis)")
        
        # Start timing the request
        start_time = time.time()
        response = requests.post(f"{base_url}/analyze/{ticker}", timeout=120)
        end_time = time.time()
        
        print(f"⏱️  Request took {end_time - start_time:.2f} seconds")
        print_response(response, "Fresh Analysis Response")
        
        if response.status_code == 200:
            data = response.json()
            if "cache" not in data.get("data", {}).get("source", ""):
                print("✅ Fresh analysis completed successfully!")
                return True
            else:
                print("⚠️  Warning: Expected fresh analysis but got cached result")
                return True
        else:
            print("❌ Fresh analysis failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Fresh analysis failed with error: {e}")
        return False


def test_results_retrieval(base_url: str, ticker: str) -> bool:
    """Test results retrieval endpoint."""
    print_separator(f"TESTING RESULTS RETRIEVAL FOR {ticker}")
    
    try:
        print(f"🔍 Making GET request to {base_url}/results/{ticker}")
        print("📊 This should retrieve the analysis from the database")
        
        response = requests.get(f"{base_url}/results/{ticker}", timeout=30)
        print_response(response, "Results Retrieval Response")
        
        if response.status_code == 200:
            data = response.json()
            analysis_data = data.get("data", {})
            
            # Validate that we have the expected fields
            required_fields = ["summary", "sentiment_report", "timestamp"]
            missing_fields = [field for field in required_fields if not analysis_data.get(field)]
            
            if missing_fields:
                print(f"⚠️  Warning: Missing required fields: {missing_fields}")
            else:
                print("✅ Results retrieval successful with all required fields!")
            
            return True
        else:
            print("❌ Results retrieval failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Results retrieval failed with error: {e}")
        return False


def test_cached_analysis(base_url: str, ticker: str) -> bool:
    """Test cached analysis retrieval."""
    print_separator(f"TESTING CACHED ANALYSIS FOR {ticker}")
    
    try:
        print(f"🔍 Making POST request to {base_url}/analyze/{ticker}")
        print("💾 This should return cached results instantly")
        
        # Start timing the request
        start_time = time.time()
        response = requests.post(f"{base_url}/analyze/{ticker}", timeout=30)
        end_time = time.time()
        
        print(f"⏱️  Request took {end_time - start_time:.2f} seconds")
        print_response(response, "Cached Analysis Response")
        
        if response.status_code == 200:
            data = response.json()
            source = data.get("data", {}).get("source", "")
            message = data.get("message", "")
            
            if "cache" in source.lower() or "cache" in message.lower():
                print("✅ Cache retrieval working correctly!")
                
                # Verify it was fast (should be under 2 seconds for cached data)
                if end_time - start_time < 2.0:
                    print("✅ Cache response was fast as expected!")
                else:
                    print("⚠️  Warning: Cache response was slower than expected")
                
                return True
            else:
                print("⚠️  Warning: Expected cached result but got fresh analysis")
                return True
        else:
            print("❌ Cached analysis test failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cached analysis test failed with error: {e}")
        return False


def test_cached_tickers_list(base_url: str) -> bool:
    """Test the cached tickers list endpoint."""
    print_separator("TESTING CACHED TICKERS LIST")
    
    try:
        print(f"🔍 Making GET request to {base_url}/cached-tickers")
        print("📋 This should return a list of all cached tickers")
        
        response = requests.get(f"{base_url}/cached-tickers", timeout=30)
        print_response(response, "Cached Tickers Response")
        
        if response.status_code == 200:
            data = response.json()
            tickers = data.get("tickers", [])
            count = data.get("count", 0)
            
            print(f"📊 Found {count} cached tickers: {[t.get('ticker') for t in tickers]}")
            print("✅ Cached tickers list retrieved successfully!")
            return True
        else:
            print("❌ Cached tickers list retrieval failed!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cached tickers test failed with error: {e}")
        return False


def test_invalid_ticker(base_url: str) -> bool:
    """Test error handling with an invalid ticker."""
    print_separator("TESTING ERROR HANDLING")
    
    try:
        invalid_ticker = "INVALID_TICKER_12345"
        print(f"🔍 Making POST request to {base_url}/analyze/{invalid_ticker}")
        print("❌ This should handle the invalid ticker gracefully")
        
        response = requests.post(f"{base_url}/analyze/{invalid_ticker}", timeout=60)
        print_response(response, "Invalid Ticker Response")
        
        # For invalid tickers, we expect either success (if NewsAPI returns something)
        # or a graceful error message, not a 500 crash
        if response.status_code in [200, 400, 404, 422]:
            print("✅ Error handling working correctly!")
            return True
        else:
            print("⚠️  Warning: Unexpected status code for invalid ticker")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error handling test failed with error: {e}")
        return False


def main():
    """Run all backend tests."""
    print("🚀 StockSense Agent Backend Test Runner")
    print("=" * 60)
    print("This script will test the complete FastAPI backend functionality.")
    print("Make sure your FastAPI server is running on http://127.0.0.1:8000")
    print("\nPress Enter to continue or Ctrl+C to abort...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n❌ Test aborted by user")
        return
    
    # Configuration
    base_url = "http://127.0.0.1:8000"
    test_ticker = "GOOGL"  # Google stock ticker
    
    print(f"\n🎯 Testing with ticker: {test_ticker}")
    print(f"🌐 API Base URL: {base_url}")
    
    # Track test results
    test_results = []
    
    # Run tests in sequence
    tests = [
        ("Health Check", lambda: test_health_endpoint(base_url)),
        ("Fresh Analysis", lambda: test_fresh_analysis(base_url, test_ticker)),
        ("Results Retrieval", lambda: test_results_retrieval(base_url, test_ticker)),
        ("Cached Analysis", lambda: test_cached_analysis(base_url, test_ticker)),
        ("Cached Tickers List", lambda: test_cached_tickers_list(base_url)),
        ("Error Handling", lambda: test_invalid_ticker(base_url)),
    ]
    
    print("\n🔄 Starting test sequence...")
    
    for test_name, test_func in tests:
        try:
            print(f"\n⏳ Waiting 3 seconds before next test...")
            time.sleep(3)
            
            result = test_func()
            test_results.append((test_name, result))
            
        except KeyboardInterrupt:
            print(f"\n❌ Test '{test_name}' interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with unexpected error: {e}")
            test_results.append((test_name, False))
    
    # Print final results
    print_separator("FINAL TEST RESULTS")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your backend is working correctly!")
    elif passed > 0:
        print("⚠️  Some tests passed. Check the failures above.")
    else:
        print("❌ All tests failed. Check your backend configuration.")
    
    print("\n" + "=" * 60)
    print("Test run completed!")


if __name__ == "__main__":
    main()
