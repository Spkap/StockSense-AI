import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, AnalysisCache

def _resolve_db_path() -> str:
    """Resolve database path with graceful fallbacks."""
    logger = logging.getLogger("stocksense.database")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels: db/ -> stocksense/ -> project_root/
    project_root = os.path.dirname(os.path.dirname(current_dir))

    env_path = os.getenv("STOCKSENSE_DB_PATH")
    candidates = []

    if env_path:
        abs_env_path = os.path.abspath(env_path)
        candidates.append(abs_env_path)
        if abs_env_path.startswith("/var/") and not os.getenv("RENDER"):
            data_dir = os.path.join(project_root, "data")
            os.makedirs(data_dir, exist_ok=True)
            candidates.append(os.path.join(data_dir, os.path.basename(abs_env_path)))

    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    candidates.append(os.path.join(data_dir, "stocksense.db"))

    candidates.append(os.path.join(project_root, "stocksense.db"))

    chosen_path = None
    for path in candidates:
        dir_path = os.path.dirname(path)
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            chosen_path = path
            break
        except (PermissionError, OSError) as e:
            logger.debug(f"Path not writable, trying next candidate: {dir_path} ({e})")
            continue

    if chosen_path is None:
        logger.error("No writable path for SQLite DB; using in-memory database.")
        return ":memory:"

    if env_path and os.path.abspath(env_path) != chosen_path:
        logger.info(
            "Using fallback database path %s (env path not writable: %s)",
            chosen_path,
            env_path,
        )

    return chosen_path


DB_PATH = _resolve_db_path()
ENGINE = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)

def init_db() -> None:
    """Initialize the database and create tables."""
    try:
        Base.metadata.create_all(bind=ENGINE)
    except SQLAlchemyError as e:
        logging.error(f"Error initializing database: {e}")
        raise


def save_analysis(
    ticker: str,
    summary: str,
    sentiment_report: str,
    price_data: Optional[List[Dict[str, Any]]] = None,
    headlines: Optional[List[str]] = None,
    reasoning_steps: Optional[List[str]] = None,
    tools_used: Optional[List[str]] = None,
    iterations: int = 0
) -> None:
    """Save analysis results with full data to the database cache."""
    session = SessionLocal()
    try:
        new_analysis = AnalysisCache(
            ticker=ticker.upper(),
            analysis_summary=summary,
            sentiment_report=sentiment_report,
            price_data_json=json.dumps(price_data or []),
            headlines_json=json.dumps(headlines or []),
            reasoning_steps_json=json.dumps(reasoning_steps or []),
            tools_used_json=json.dumps(tools_used or []),
            iterations=iterations,
            timestamp=datetime.utcnow()
        )
        session.add(new_analysis)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error saving analysis: {e}")
        raise
    finally:
        session.close()


def get_latest_analysis(ticker: str) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent analysis with full data for a given ticker."""
    session = SessionLocal()
    try:
        analysis = (
            session.query(AnalysisCache)
            .filter(AnalysisCache.ticker == ticker.upper())
            .order_by(desc(AnalysisCache.timestamp))
            .first()
        )
        if analysis:
            return {
                'id': analysis.id,
                'ticker': analysis.ticker,
                'analysis_summary': analysis.analysis_summary,
                'sentiment_report': analysis.sentiment_report,
                'price_data': json.loads(analysis.price_data_json or '[]'),
                'headlines': json.loads(analysis.headlines_json or '[]'),
                'reasoning_steps': json.loads(analysis.reasoning_steps_json or '[]'),
                'tools_used': json.loads(analysis.tools_used_json or '[]'),
                'iterations': analysis.iterations or 0,
                'timestamp': analysis.timestamp.isoformat(),
            }
        return None
    except SQLAlchemyError as e:
        logging.error(f"Error getting latest analysis: {e}")
        return None
    finally:
        session.close()


def delete_cached_analysis(ticker: str) -> bool:
    """Delete all cached analyses for a given ticker. Returns True if any were deleted."""
    session = SessionLocal()
    try:
        result = session.query(AnalysisCache).filter(
            AnalysisCache.ticker == ticker.upper()
        ).delete()
        session.commit()
        return result > 0
    except SQLAlchemyError as e:
        session.rollback()
        logging.error(f"Error deleting cached analysis: {e}")
        return False
    finally:
        session.close()


def get_all_cached_tickers() -> List[str]:
    """Get a list of all tickers that have cached analysis data."""
    session = SessionLocal()
    try:
        tickers = (
            session.query(AnalysisCache.ticker)
            .distinct()
            .order_by(desc(AnalysisCache.timestamp))
            .all()
        )
        return [ticker[0] for ticker in tickers]
    except SQLAlchemyError as e:
        logging.error(f"Error getting all cached tickers: {e}")
        return []
    finally:
        session.close()


def get_all_cached_tickers_with_timestamps() -> List[Dict[str, Any]]:
    """
    Get a list of all tickers with their most recent analysis timestamps.
    Returns list of dicts with 'symbol' and 'timestamp' keys.
    """
    session = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Get the most recent analysis for each ticker
        subquery = (
            session.query(
                AnalysisCache.ticker,
                func.max(AnalysisCache.timestamp).label('latest_timestamp')
            )
            .group_by(AnalysisCache.ticker)
            .subquery()
        )
        
        results = (
            session.query(subquery.c.ticker, subquery.c.latest_timestamp)
            .order_by(subquery.c.latest_timestamp.desc())
            .all()
        )
        
        return [
            {
                "symbol": row[0],
                "timestamp": row[1].isoformat() if row[1] else None
            }
            for row in results
        ]
    except SQLAlchemyError as e:
        logging.error(f"Error getting cached tickers with timestamps: {e}")
        return []
    finally:
        session.close()


if __name__ == '__main__':
    init_db()
    sample_ticker = "AAPL"
    sample_summary = "Apple showed strong performance with positive earnings."
    sample_sentiment = "Overall sentiment: Positive. Headlines show bullish outlook."
    save_analysis(sample_ticker, sample_summary, sample_sentiment)
    retrieved_data = get_latest_analysis(sample_ticker)
    print(f"Retrieved data: {retrieved_data}")
    non_existent = get_latest_analysis("NONEXISTENT")
    print(f"Non-existent data: {non_existent}")
    cached_tickers = get_all_cached_tickers()
    print(f"Cached tickers: {cached_tickers}")
    cached_with_ts = get_all_cached_tickers_with_timestamps()
    print(f"Cached tickers with timestamps: {cached_with_ts}")