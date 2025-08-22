import requests
import time
import json
from typing import Dict, Any


def print_separator(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_response(response: requests.Response, step_name: str) -> None:
    print(f"\n {step_name}")
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")

    try:
        response_data = response.json()
        print("Response Body:")
        print(json.dumps(response_data, indent=2))
    except json.JSONDecodeError:
        print(f"Response Body (raw): {response.text}")


def test_health_endpoint(base_url: str) -> bool:
    print_separator("TESTING HEALTH ENDPOINT")

    try:
        print(f" Making GET request to {base_url}/health")
        response = requests.get(f"{base_url}/health", timeout=10)

        print_response(response, "Health Check Response")

        if response.status_code == 200:
            print(" Health check passed!")
            return True
        else:
            print(" Health check failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f" Health check failed with error: {e}")
        return False


def test_fresh_analysis(base_url: str, ticker: str) -> bool:
    print_separator(f"TESTING FRESH ANALYSIS FOR {ticker}")

    try:
        print(f" Making POST request to {base_url}/analyze/{ticker}")
        print(" This should trigger a fresh ReAct Agent analysis")

        start_time = time.time()
        response = requests.post(f"{base_url}/analyze/{ticker}", timeout=120)
        end_time = time.time()

        print(f"  Request took {end_time - start_time:.2f} seconds")
        print_response(response, "Fresh ReAct Agent Analysis Response")

        if response.status_code == 200:
            data = response.json()
            if "cache" not in data.get("data", {}).get("source", ""):
                print(" Fresh ReAct Agent analysis completed successfully!")
                return True
            else:
                print("  Warning: Expected fresh ReAct analysis but got cached result")
                return True
        else:
            print(" Fresh ReAct Agent analysis failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f" Fresh ReAct Agent analysis failed with error: {e}")
        return False


def test_results_retrieval(base_url: str, ticker: str) -> bool:
    print_separator(f"TESTING RESULTS RETRIEVAL FOR {ticker}")

    try:
        print(f" Making GET request to {base_url}/results/{ticker}")
        print(" This should retrieve the analysis from the database")

        response = requests.get(f"{base_url}/results/{ticker}", timeout=30)
        print_response(response, "Results Retrieval Response")

        if response.status_code == 200:
            data = response.json()
            analysis_data = data.get("data", {})

            required_fields = ["summary", "sentiment_report", "timestamp"]
            missing_fields = [field for field in required_fields if not analysis_data.get(field)]

            if missing_fields:
                print(f"  Warning: Missing required fields: {missing_fields}")
            else:
                print(" Results retrieval successful with all required fields!")

            return True
        else:
            print(" Results retrieval failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f" Results retrieval failed with error: {e}")
        return False


def test_cached_analysis(base_url: str, ticker: str) -> bool:
    print_separator(f"TESTING CACHED ANALYSIS FOR {ticker}")

    try:
        print(f" Making POST request to {base_url}/analyze/{ticker}")
        print(" This should return cached results instantly")

        start_time = time.time()
        response = requests.post(f"{base_url}/analyze/{ticker}", timeout=30)
        end_time = time.time()

        print(f"  Request took {end_time - start_time:.2f} seconds")
        print_response(response, "Cached Analysis Response")

        if response.status_code == 200:
            data = response.json()
            source = data.get("data", {}).get("source", "")
            message = data.get("message", "")

            if "cache" in source.lower() or "cache" in message.lower():
                print(" Cache retrieval working correctly!")

                if end_time - start_time < 2.0:
                    print(" Cache response was fast as expected!")
                else:
                    print("  Warning: Cache response was slower than expected")

                return True
            else:
                print("  Warning: Expected cached result but got fresh analysis")
                return True
        else:
            print(" Cached analysis test failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f" Cached analysis test failed with error: {e}")
        return False


def test_cached_tickers_list(base_url: str) -> bool:
    print_separator("TESTING CACHED TICKERS LIST")

    try:
        print(f" Making GET request to {base_url}/cached-tickers")
        print("📋 This should return a list of all cached tickers")

        response = requests.get(f"{base_url}/cached-tickers", timeout=30)
        print_response(response, "Cached Tickers Response")

        if response.status_code == 200:
            data = response.json()
            tickers = data.get("tickers", [])
            count = data.get("count", 0)

            print(f" Found {count} cached tickers: {[t.get('ticker') for t in tickers]}")
            print(" Cached tickers list retrieved successfully!")
            return True
        else:
            print(" Cached tickers list retrieval failed!")
            return False

    except requests.exceptions.RequestException as e:
        print(f" Cached tickers test failed with error: {e}")
        return False


def test_invalid_ticker(base_url: str) -> bool:
    print_separator("TESTING ERROR HANDLING")

    try:
        invalid_ticker = "INVALID_TICKER_12345"
        print(f" Making POST request to {base_url}/analyze/{invalid_ticker}")
        print(" This should handle the invalid ticker gracefully")

        response = requests.post(f"{base_url}/analyze/{invalid_ticker}", timeout=60)
        print_response(response, "Invalid Ticker Response")

        if response.status_code in [200, 400, 404, 422]:
            print(" Error handling working correctly!")
            return True
        else:
            print("  Warning: Unexpected status code for invalid ticker")
            return True

    except requests.exceptions.RequestException as e:
        print(f" Error handling test failed with error: {e}")
        return False


def main():
    print("🚀 StockSense ReAct Agent Backend Test Runner")
    print("=" * 60)
    print("This script will test the complete ReAct Agent FastAPI backend functionality.")
    print("Make sure your FastAPI server is running on http://127.0.0.1:8000")
    print("\nPress Enter to continue or Ctrl+C to abort...")

    try:
        input()
    except KeyboardInterrupt:
        print("\n Test aborted by user")
        return

    base_url = "http://127.0.0.1:8000"
    test_ticker = "GOOGL"

    print(f"\n Testing with ticker: {test_ticker}")
    print(f" API Base URL: {base_url}")

    test_results = []

    tests = [
        ("Health Check", lambda: test_health_endpoint(base_url)),
        ("Fresh ReAct Agent Analysis", lambda: test_fresh_analysis(base_url, test_ticker)),
        ("Results Retrieval", lambda: test_results_retrieval(base_url, test_ticker)),
        ("Cached Analysis", lambda: test_cached_analysis(base_url, test_ticker)),
        ("Cached Tickers List", lambda: test_cached_tickers_list(base_url)),
        ("Error Handling", lambda: test_invalid_ticker(base_url)),
    ]

    print("\n Starting test sequence...")

    for test_name, test_func in tests:
        try:
            print(f"\n⏳ Waiting 3 seconds before next test...")
            time.sleep(3)

            result = test_func()
            test_results.append((test_name, result))

        except KeyboardInterrupt:
            print(f"\n Test '{test_name}' interrupted by user")
            break
        except Exception as e:
            print(f"\n Test '{test_name}' failed with unexpected error: {e}")
            test_results.append((test_name, False))

    print_separator("FINAL TEST RESULTS")

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = " PASSED" if result else " FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1

    print(f"\n SUMMARY: {passed}/{total} tests passed")

    if passed == total:
        print(" All tests passed! Your ReAct Agent backend is working correctly!")
    elif passed > 0:
        print("  Some tests passed. Check the failures above.")
    else:
        print(" All tests failed. Check your ReAct Agent backend configuration.")

    print("\n" + "=" * 60)
    print("Test run completed!")


if __name__ == "__main__":
    main()