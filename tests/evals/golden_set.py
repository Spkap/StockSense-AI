"""
Golden test set for StockSense eval harness.

Each case defines:
  - ticker: The stock symbol
  - mock_headlines: Deterministic headlines (no live NewsAPI call)
  - mock_fundamentals: Deterministic fundamentals (no live yfinance call)
  - mock_price_data: Deterministic OHLCV price data
  - expectations: Ranges/values the analysis output must satisfy

Add cases here before changing any prompts.
Run eval_runner.py after changes to measure regression.
"""

GOLDEN_SET = [
    {
        "ticker": "AAPL",
        "mock_headlines": [
            "Apple beats Q4 earnings by $0.15 per share",
            "iPhone 17 demand exceeds analyst expectations",
            "Apple services revenue hits all-time high",
            "Apple faces EU antitrust investigation",
            "Apple announces $110B share buyback program",
        ],
        "mock_fundamentals": {
            "info": {
                "revenue_growth": 0.08,
                "market_cap": 3_400_000_000_000,
                "forward_pe": 28.5,
                "trailingPE": 32.1,
                "debtToEquity": 180.0,
                "profitMargins": 0.26,
                "shortRatio": 0.8,
                "recommendation_mean": 1.8,
            }
        },
        "mock_price_data": [
            {"date": f"2026-01-{i+1:02d}", "close": 220.0 + i * 0.3}
            for i in range(60)
        ],
        "expectations": {
            "bull_confidence_min": 0.5,
            "bear_confidence_min": 0.3,
            "bull_thesis_non_empty": True,
            "bear_thesis_non_empty": True,
        },
    },
    {
        "ticker": "TSLA",
        "mock_headlines": [
            "Tesla misses Q3 delivery estimates by 8%",
            "Tesla faces increased competition from BYD",
            "Tesla Cybertruck recall issued for accelerator issue",
            "Tesla energy storage business doubles revenue",
            "Elon Musk sells $2B in Tesla stock",
        ],
        "mock_fundamentals": {
            "info": {
                "revenue_growth": -0.03,
                "market_cap": 800_000_000_000,
                "forward_pe": 65.0,
                "trailingPE": 70.0,
                "debtToEquity": 19.0,
                "profitMargins": 0.08,
                "shortRatio": 3.2,
                "recommendation_mean": 2.9,
            }
        },
        "mock_price_data": [
            {"date": f"2026-01-{i+1:02d}", "close": 300.0 - i * 0.8}
            for i in range(60)
        ],
        "expectations": {
            "bull_confidence_min": 0.2,
            "bear_confidence_min": 0.5,
            "bull_thesis_non_empty": True,
            "bear_thesis_non_empty": True,
        },
    },
    {
        "ticker": "MSFT",
        "mock_headlines": [
            "Microsoft Azure revenue grows 31% year over year",
            "Microsoft Copilot adoption reaches 100M users",
            "Microsoft beats EPS estimates for fifth consecutive quarter",
            "Microsoft faces EU cloud competition concerns",
            "Microsoft raises quarterly dividend by 10%",
        ],
        "mock_fundamentals": {
            "info": {
                "revenue_growth": 0.16,
                "market_cap": 3_100_000_000_000,
                "forward_pe": 30.2,
                "trailingPE": 35.0,
                "debtToEquity": 42.0,
                "profitMargins": 0.36,
                "shortRatio": 0.6,
                "recommendation_mean": 1.5,
            }
        },
        "mock_price_data": [
            {"date": f"2026-01-{i+1:02d}", "close": 420.0 + i * 0.5}
            for i in range(60)
        ],
        "expectations": {
            "bull_confidence_min": 0.55,
            "bear_confidence_min": 0.25,
            "bull_thesis_non_empty": True,
            "bear_thesis_non_empty": True,
        },
    },
    {
        "ticker": "NVDA",
        "mock_headlines": [
            "Nvidia reports record data center revenue of $47B",
            "Nvidia Blackwell chip demand exceeds supply",
            "US considers further AI chip export restrictions on Nvidia",
            "Nvidia stock up 200% year to date",
            "Nvidia faces antitrust scrutiny over market dominance",
        ],
        "mock_fundamentals": {
            "info": {
                "revenue_growth": 1.22,
                "market_cap": 3_300_000_000_000,
                "forward_pe": 38.0,
                "trailingPE": 55.0,
                "debtToEquity": 45.0,
                "profitMargins": 0.55,
                "shortRatio": 0.9,
                "recommendation_mean": 1.4,
            }
        },
        "mock_price_data": [
            {"date": f"2026-01-{i+1:02d}", "close": 900.0 + i * 2.0}
            for i in range(60)
        ],
        "expectations": {
            "bull_confidence_min": 0.55,
            "bear_confidence_min": 0.3,
            "bull_thesis_non_empty": True,
            "bear_thesis_non_empty": True,
        },
    },
    {
        "ticker": "GS",
        "mock_headlines": [
            "Goldman Sachs Q2 trading revenue beats estimates",
            "Goldman Sachs faces DOJ probe over bond trading practices",
            "Goldman Sachs cuts 800 jobs in restructuring",
            "Goldman Sachs raises full-year profit guidance",
            "Goldman Sachs consumer banking unit losses widen",
        ],
        "mock_fundamentals": {
            "info": {
                "revenue_growth": 0.04,
                "market_cap": 175_000_000_000,
                "forward_pe": 12.8,
                "trailingPE": 14.2,
                "debtToEquity": 580.0,
                "profitMargins": 0.18,
                "shortRatio": 1.8,
                "recommendation_mean": 2.1,
            }
        },
        "mock_price_data": [
            {"date": f"2026-01-{i+1:02d}", "close": 520.0 + (i % 5) * 2.0}
            for i in range(60)
        ],
        "expectations": {
            "bull_confidence_min": 0.3,
            "bear_confidence_min": 0.3,
            "bull_thesis_non_empty": True,
            "bear_thesis_non_empty": True,
        },
    },
]
