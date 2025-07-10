"""
Database module for StockSense Agent.

This module provides functions to cache stock analysis results using SQLite
to avoid re-computing analysis for previously analyzed tickers.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional


def init_db() -> None:
    """
    Initialize the SQLite database and create the analysis_cache table if it doesn't exist.
    
    The database file 'stocksense.db' will be created in the project root directory.
    """
    try:
        # Get the project root directory (one level up from this file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        print(f"Initializing database at: {db_path}")
        
        # Connect to the database (creates file if it doesn't exist)
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Create the analysis_cache table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    analysis_summary TEXT,
                    sentiment_report TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            # Create an index on ticker and timestamp for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker_timestamp 
                ON analysis_cache (ticker, timestamp DESC)
            ''')
            
            # Commit the changes
            conn.commit()
            print("Database initialized successfully!")
        
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise


def save_analysis(ticker: str, summary: str, sentiment_report: str) -> None:
    """
    Save analysis results to the database cache.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        summary (str): Analysis summary text
        sentiment_report (str): Sentiment analysis report
    """
    try:
        # Get the project root directory and database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        # Generate current timestamp in ISO format (UTC)
        timestamp = datetime.utcnow().isoformat()
        
        print(f"Saving analysis for {ticker} to database...")
        
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Insert the analysis data
            cursor.execute('''
                INSERT INTO analysis_cache (ticker, analysis_summary, sentiment_report, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (ticker.upper(), summary, sentiment_report, timestamp))
            
            # Commit the changes
            conn.commit()
            print(f"Analysis for {ticker} saved successfully!")
        
    except sqlite3.Error as e:
        print(f"Error saving analysis for {ticker}: {e}")
        raise


def get_latest_analysis(ticker: str) -> Optional[Dict[str, str]]:
    """
    Retrieve the most recent analysis for a given ticker from the database cache.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'NVDA')
    
    Returns:
        Dict[str, str] or None: Dictionary containing the analysis data if found,
                               None if no analysis exists for the ticker
    """
    try:
        # Get the project root directory and database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print("Database not found. Run init_db() first.")
            return None
        
        print(f"Checking cache for {ticker}...")
        
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Query for the most recent analysis for the ticker
            cursor.execute('''
                SELECT id, ticker, analysis_summary, sentiment_report, timestamp
                FROM analysis_cache 
                WHERE ticker = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (ticker.upper(),))
            
            result = cursor.fetchone()
            
            if result:
                # Convert result to dictionary
                analysis_data = {
                    'id': result[0],
                    'ticker': result[1],
                    'analysis_summary': result[2],
                    'sentiment_report': result[3],
                    'timestamp': result[4]
                }
                print(f"Found cached analysis for {ticker} from {result[4]}")
                return analysis_data
            else:
                print(f"No cached analysis found for {ticker}")
                return None
            
    except sqlite3.Error as e:
        print(f"Error retrieving analysis for {ticker}: {e}")
        return None


def get_all_cached_tickers() -> list:
    """
    Get a list of all tickers that have cached analysis data.
    
    Returns:
        list: List of ticker symbols that have cached data
    """
    try:
        # Get the project root directory and database path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print("Database not found. Run init_db() first.")
            return []
        
        # Connect to the database
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Query for all unique tickers with their most recent timestamp
            cursor.execute('''
                SELECT DISTINCT ticker, MAX(timestamp) as latest_timestamp
                FROM analysis_cache 
                GROUP BY ticker
                ORDER BY latest_timestamp DESC
            ''')
            
            results = cursor.fetchall()
            tickers = [result[0] for result in results]
            
            print(f"Found {len(tickers)} tickers with cached analysis")
            return tickers
        
    except sqlite3.Error as e:
        print(f"Error retrieving cached tickers: {e}")
        return []


if __name__ == '__main__':
    """
    Test the database functionality.
    """
    print("=" * 60)
    print("Testing StockSense Database Module")
    print("=" * 60)
    
    # Test 1: Initialize database
    print("\n1. Testing database initialization:")
    print("-" * 40)
    init_db()
    
    # Test 2: Save sample analysis
    print("\n2. Testing save_analysis:")
    print("-" * 40)
    sample_ticker = "AAPL"
    sample_summary = "Apple showed strong performance with positive earnings."
    sample_sentiment = "Overall sentiment: Positive. Headlines show bullish outlook."
    
    save_analysis(sample_ticker, sample_summary, sample_sentiment)
    
    # Test 3: Retrieve analysis
    print("\n3. Testing get_latest_analysis:")
    print("-" * 40)
    retrieved_data = get_latest_analysis(sample_ticker)
    
    if retrieved_data:
        print(f"Retrieved analysis for {retrieved_data['ticker']}:")
        print(f"Timestamp: {retrieved_data['timestamp']}")
        print(f"Summary: {retrieved_data['analysis_summary'][:100]}...")
        print(f"Sentiment: {retrieved_data['sentiment_report'][:100]}...")
    else:
        print("No data retrieved")
    
    # Test 4: Test with non-existent ticker
    print("\n4. Testing with non-existent ticker:")
    print("-" * 40)
    non_existent = get_latest_analysis("NONEXISTENT")
    print(f"Result for non-existent ticker: {non_existent}")
    
    # Test 5: Get all cached tickers
    print("\n5. Testing get_all_cached_tickers:")
    print("-" * 40)
    cached_tickers = get_all_cached_tickers()
    print(f"Cached tickers: {cached_tickers}")
    
    print("\n" + "=" * 60)
    print("Database testing completed!")
    print("=" * 60)