#!/usr/bin/env python3
"""
StockSense Agent - Main Pipeline Script (Week 1)

This script serves as the main entry point for the StockSense Agent application.
It orchestrates the complete data collection and sentiment analysis pipeline
for stock market research.

Usage:
    python run_pipeline.py
"""

import sys
from typing import List
from stocksense.data_collectors import get_news, get_price_history
from stocksense.analyzer import analyze_sentiment_of_headlines


def run_full_pipeline(ticker: str) -> None:
    """
    Execute the complete StockSense analysis pipeline for a given stock ticker.
    
    This function orchestrates the entire workflow:
    1. Fetches recent news headlines for the ticker
    2. Performs AI-powered sentiment analysis on the headlines
    3. Displays a comprehensive sentiment analysis report
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'MSFT', 'NVDA')
    """
    print("=" * 80)
    print(f"📈 STOCKSENSE AGENT - SENTIMENT ANALYSIS PIPELINE")
    print("=" * 80)
    print(f"🎯 Target Stock: {ticker.upper()}")
    print(f"🤖 Powered by AI-driven sentiment analysis")
    print("=" * 80)
    
    try:
        # Step 1: Data Collection - News Headlines
        print("\n🔍 STEP 1: Fetching recent news headlines...")
        print("-" * 50)
        
        headlines = get_news(ticker, days=7)
        
        if not headlines:
            print(f"❌ No news headlines found for {ticker.upper()}")
            print("   This could be due to:")
            print("   - Invalid ticker symbol")
            print("   - No recent news coverage")
            print("   - API key issues")
            print("\n💡 Please try a different ticker or check your NewsAPI configuration.")
            return
        
        print(f"✅ Successfully collected {len(headlines)} headlines")
        print(f"📰 Sample headlines:")
        for i, headline in enumerate(headlines[:3], 1):
            print(f"   {i}. {headline}")
        if len(headlines) > 3:
            print(f"   ... and {len(headlines) - 3} more headlines")
        
        # Step 2: AI-Powered Sentiment Analysis
        print(f"\n🧠 STEP 2: Analyzing sentiment with AI...")
        print("-" * 50)
        
        sentiment_analysis = analyze_sentiment_of_headlines(headlines)
        
        if not sentiment_analysis or "Error" in sentiment_analysis:
            print(f"❌ Sentiment analysis failed for {ticker.upper()}")
            print("   This could be due to:")
            print("   - Google API key issues")
            print("   - Network connectivity problems")
            print("   - API rate limits")
            print("\n💡 Please check your Google API configuration.")
            return
        
        # Step 3: Display Comprehensive Report
        print(f"\n📊 STEP 3: Generating sentiment analysis report...")
        print("-" * 50)
        print("✅ Analysis completed successfully!")
        
        print(f"\n" + "=" * 80)
        print(f"📈 SENTIMENT ANALYSIS REPORT FOR {ticker.upper()}")
        print("=" * 80)
        print(f"📅 Analysis Date: {get_current_timestamp()}")
        print(f"📰 Headlines Analyzed: {len(headlines)}")
        print(f"🤖 AI Model: Google Gemini 1.5 Flash")
        print("=" * 80)
        
        print(sentiment_analysis)
        
        print("\n" + "=" * 80)
        print("🎉 PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("💡 Next Steps:")
        print("   - Review the sentiment analysis above")
        print("   - Consider the market implications")
        print("   - Use insights for informed investment decisions")
        print("=" * 80)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Please ensure all required packages are installed:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected error during pipeline execution: {e}")
        print("💡 Please check your configuration and try again.")
        sys.exit(1)


def get_current_timestamp() -> str:
    """
    Get the current timestamp in a readable format.
    
    Returns:
        str: Formatted timestamp string
    """
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def display_pipeline_info() -> None:
    """
    Display information about the StockSense pipeline capabilities.
    """
    print("\n" + "=" * 80)
    print("ℹ️  STOCKSENSE AGENT - PIPELINE INFORMATION")
    print("=" * 80)
    print("This pipeline performs the following analysis:")
    print("📰 1. News Collection: Fetches recent headlines from NewsAPI")
    print("🧠 2. AI Analysis: Uses Google Gemini for sentiment analysis")
    print("📊 3. Market Insights: Provides investment-relevant insights")
    print("\n🔧 Current Configuration:")
    print("   - News Source: NewsAPI (last 7 days)")
    print("   - AI Model: Google Gemini 1.5 Flash")
    print("   - Analysis Scope: Headlines sentiment + market impact")
    print("=" * 80)


if __name__ == '__main__':
    """
    Main execution block for testing the pipeline.
    """
    # Display pipeline information
    display_pipeline_info()
    
    # Default ticker for testing
    test_ticker = "MSFT"
    
    print(f"\n🚀 Starting pipeline execution with test ticker: {test_ticker}")
    print("=" * 80)
    
    # Execute the full pipeline
    run_full_pipeline(test_ticker)
    
    print(f"\n💡 To analyze a different stock, modify the 'test_ticker' variable")
    print(f"   or call: run_full_pipeline('YOUR_TICKER')")
    
    # Optional: Demonstrate with another ticker
    print(f"\n" + "=" * 80)
    print("🔄 BONUS: Running pipeline for another ticker (AAPL)")
    print("=" * 80)
    run_full_pipeline("AAPL")