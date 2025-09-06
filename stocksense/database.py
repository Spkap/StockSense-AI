import sqlite3
import os
from datetime import datetime
from typing import Dict, Optional


def _resolve_db_path() -> str:
    """Resolve database path allowing override with STOCKSENSE_DB_PATH env var.

    Falls back to project root 'stocksense.db' if not specified. Ensures directory exists.
    """
    # Allow explicit override
    env_path = os.getenv("STOCKSENSE_DB_PATH")
    if env_path:
        db_path = os.path.abspath(env_path)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        db_path = os.path.join(project_root, 'stocksense.db')

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


def init_db() -> None:
    try:
        db_path = _resolve_db_path()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL") # For better concurrency
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

    except sqlite3.Error as e:
        raise
    except Exception as e:
        raise


def save_analysis(ticker: str, summary: str, sentiment_report: str) -> None:
    """Save analysis results to the database cache."""
    try:
        db_path = _resolve_db_path()

        if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
            init_db()

        timestamp = datetime.utcnow().isoformat()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_cache'")
            table_exists = cursor.fetchone()

            if not table_exists:
                conn.close()
                init_db()
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO analysis_cache (ticker, analysis_summary, sentiment_report, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (ticker.upper(), summary, sentiment_report, timestamp))

            conn.commit()

    except sqlite3.Error as e:
        raise
    except Exception as e:
        raise


def get_latest_analysis(ticker: str) -> Optional[Dict[str, str]]:
    """Retrieve the most recent analysis for a given ticker."""
    try:
        db_path = _resolve_db_path()

        if not os.path.exists(db_path):
            return None

        if os.path.getsize(db_path) == 0:
            init_db()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_cache'")
            table_exists = cursor.fetchone()

            if not table_exists:
                conn.close()
                init_db()
                conn = sqlite3.connect(db_path)
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
                return analysis_data
            else:
                return None

    except sqlite3.Error as e:
        return None
    except Exception as e:
        return None


def get_all_cached_tickers() -> list:
    """Get a list of all tickers that have cached analysis data."""
    try:
        db_path = _resolve_db_path()

        if not os.path.exists(db_path):
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

            return tickers

    except sqlite3.Error as e:
        return []


if __name__ == '__main__':
    init_db()
    sample_ticker = "AAPL"
    sample_summary = "Apple showed strong performance with positive earnings."
    sample_sentiment = "Overall sentiment: Positive. Headlines show bullish outlook."
    save_analysis(sample_ticker, sample_summary, sample_sentiment)
    retrieved_data = get_latest_analysis(sample_ticker)
    non_existent = get_latest_analysis("NONEXISTENT")
    cached_tickers = get_all_cached_tickers()