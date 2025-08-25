# StockSense Agent Test Suite

This directory contains the automated test suite for the StockSense Agent project.

## Test Structure

### Unit Tests (`test_tools.py`)

Tests for individual agent tools without external dependencies:

- `fetch_news_headlines` tool functionality
- `fetch_price_data` tool functionality
- Error handling for invalid tickers
- Data structure validation

### Integration Tests (`test_api.py`)

Tests for the FastAPI application endpoints:

- Health check endpoint (`/health`)
- Cached tickers endpoint (`/cached-tickers`)
- API response format validation
- Error handling and performance

## Running Tests

### Prerequisites

```bash
# Install pytest if not already installed
pip install pytest requests
```

### Quick Start

```bash
# Run all tests
python run_tests.py all

# Run only unit tests (no server required)
python run_tests.py unit

# Run only API tests (requires server running)
python run_tests.py api

# Run quick smoke test
python run_tests.py smoke
```

### Manual pytest Commands

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/test_tools.py -v

# Run only API tests
pytest tests/test_api.py -v

# Run with coverage (if coverage installed)
pytest tests/ --cov=stocksense --cov-report=html
```

## Test Requirements

### For Unit Tests

- No external dependencies
- Tests the tools in isolation
- Validates data structures and error handling

### For API Tests

- Requires the FastAPI server to be running
- Start server with: `python -m stocksense.main`
- Tests live HTTP endpoints

## Test Configuration

The test suite is configured via `pytest.ini` with:

- Test discovery patterns
- Output formatting
- Timeout settings
- Custom markers for test categorization

## Adding New Tests

### Unit Test Example

```python
def test_new_tool_functionality():
    """Test a new tool function"""
    result = new_tool.invoke({"param": "value"})
    assert isinstance(result, dict)
    assert "expected_key" in result
```

### API Test Example

```python
def test_new_endpoint():
    """Test a new API endpoint"""
    response = requests.get(f"{BASE_URL}/new-endpoint")
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

## Continuous Integration

These tests are designed to be CI/CD friendly:

- Unit tests can run without external dependencies
- API tests can be skipped if server isn't available
- Clear exit codes for success/failure
- Detailed output for debugging

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure the project root is in Python path
2. **API Tests Failing**: Make sure the FastAPI server is running
3. **Network Tests Slow**: Use `-m "not network"` to skip network-dependent tests
4. **Tool Tests Failing**: Check if external data sources (news, price data) are accessible

### Debug Mode

```bash
# Run with more verbose output
pytest tests/ -v -s --tb=long

# Run a specific test
pytest tests/test_tools.py::TestNewsHeadlines::test_fetch_news_headlines_success -v
```
