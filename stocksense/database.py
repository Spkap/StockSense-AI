"""
Database module for StockSense ReAct Agent.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional


def init_db() -> None:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        print(f"Initializing database at: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    analysis_summary TEXT,
                    sentiment_report TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_ticker_timestamp 
                ON analysis_cache (ticker, timestamp DESC)
            ''')
            
            conn.commit()
            print("Database initialized successfully!")
        
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
        raise


def save_analysis(ticker: str, summary: str, sentiment_report: str) -> None:
    """Save analysis results to the database cache."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        timestamp = datetime.utcnow().isoformat()
        
        print(f"Saving analysis for {ticker} to database...")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO analysis_cache (ticker, analysis_summary, sentiment_report, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (ticker.upper(), summary, sentiment_report, timestamp))
            
            conn.commit()
            print(f"Analysis for {ticker} saved successfully!")
        
    except sqlite3.Error as e:
        print(f"Error saving analysis for {ticker}: {e}")
        raise


def get_latest_analysis(ticker: str) -> Optional[Dict[str, str]]:
    """Retrieve the most recent analysis for a given ticker."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        if not os.path.exists(db_path):
            print("Database not found. Run init_db() first.")
            return None
        
        print(f"Checking cache for {ticker}...")
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, ticker, analysis_summary, sentiment_report, timestamp
                FROM analysis_cache 
                WHERE ticker = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            ''', (ticker.upper(),))
            
            result = cursor.fetchone()
            
            if result:
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
    """Get a list of all tickers that have cached analysis data."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')
        
        if not os.path.exists(db_path):
            print("Database not found. Run init_db() first.")
            return []
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
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
    """Test the database functionality."""
    print("=" * 60)
    print("Testing StockSense ReAct Agent Database Module")
    print("=" * 60)
    
    print("\n1. Testing database initialization:")
    print("-" * 40)
    init_db()
    
    print("\n2. Testing save_analysis:")
    print("-" * 40)
    sample_ticker = "AAPL"
    sample_summary = "Apple showed strong performance with positive earnings."
    sample_sentiment = "Overall sentiment: Positive. Headlines show bullish outlook."
    
    save_analysis(sample_ticker, sample_summary, sample_sentiment)
    
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
    
    print("\n4. Testing with non-existent ticker:")
    print("-" * 40)
    non_existent = get_latest_analysis("NONEXISTENT")
    print(f"Result for non-existent ticker: {non_existent}")
    
    print("\n5. Testing get_all_cached_tickers:")
    print("-" * 40)
    cached_tickers = get_all_cached_tickers()
    print(f"Cached tickers: {cached_tickers}")
    
    print("\n" + "=" * 60)
    print("Database testing completed!")
    print("=" * 60)