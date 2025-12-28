"""
Database module for StockSense analysis cache.

Migrated from SQLite to Supabase for production persistence.
All analysis results are stored in Supabase's `analysis_cache` table.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List, Any

from stocksense.db.supabase_client import get_supabase_client, SupabaseAuthError

logger = logging.getLogger("stocksense.database")


def init_db() -> None:
    """
    Initialize database connection.
    
    With Supabase, this just validates the connection is working.
    The actual table creation is done via SQL migrations.
    """
    try:
        client = get_supabase_client()
        # Quick connectivity check
        client.table("analysis_cache").select("id").limit(1).execute()
        logger.info("Supabase analysis_cache connection verified")
    except SupabaseAuthError as e:
        logger.error(f"Supabase connection failed: {e}")
        raise
    except Exception as e:
        # Table might not exist yet - that's okay during first deployment
        logger.warning(f"Database init check failed (table may not exist yet): {e}")


def save_analysis(
    ticker: str,
    summary: str,
    sentiment_report: str,
    price_data: Optional[List[Dict[str, Any]]] = None,
    headlines: Optional[List[str]] = None,
    reasoning_steps: Optional[List[str]] = None,
    tools_used: Optional[List[str]] = None,
    iterations: int = 0,
    # Extended fields for structured analysis
    overall_sentiment: str = "",
    overall_confidence: float = 0.0,
    confidence_reasoning: str = "",
    headline_analyses: Optional[List[Dict]] = None,
    key_themes: Optional[List[Dict]] = None,
    potential_impact: str = "",
    risks_identified: Optional[List[str]] = None,
    information_gaps: Optional[List[str]] = None,
    # Skeptic analysis fields
    skeptic_report: str = "",
    skeptic_sentiment: str = "",
    skeptic_confidence: float = 0.0,
    primary_disagreement: str = "",
    critiques: Optional[List[Dict]] = None,
    bear_cases: Optional[List[Dict]] = None,
    hidden_risks: Optional[List[str]] = None,
    would_change_mind: Optional[List[str]] = None,
    # Fundamental data
    fundamental_data: Optional[Dict] = None,
) -> Optional[Dict[str, Any]]:
    """Save analysis results to Supabase analysis_cache table."""
    try:
        client = get_supabase_client()
        
        data = {
            "ticker": ticker.upper(),
            "analysis_summary": summary,
            "sentiment_report": sentiment_report,
            "price_data": price_data or [],
            "headlines": headlines or [],
            "reasoning_steps": reasoning_steps or [],
            "tools_used": tools_used or [],
            "iterations": iterations,
            # Structured sentiment
            "overall_sentiment": overall_sentiment,
            "overall_confidence": overall_confidence,
            "confidence_reasoning": confidence_reasoning,
            "headline_analyses": headline_analyses or [],
            "key_themes": key_themes or [],
            "potential_impact": potential_impact,
            "risks_identified": risks_identified or [],
            "information_gaps": information_gaps or [],
            # Skeptic analysis
            "skeptic_report": skeptic_report,
            "skeptic_sentiment": skeptic_sentiment,
            "skeptic_confidence": skeptic_confidence,
            "primary_disagreement": primary_disagreement,
            "critiques": critiques or [],
            "bear_cases": bear_cases or [],
            "hidden_risks": hidden_risks or [],
            "would_change_mind": would_change_mind or [],
            # Fundamentals
            "fundamental_data": fundamental_data or {},
        }
        
        response = client.table("analysis_cache").insert(data).execute()
        
        if response.data:
            logger.info(f"Analysis saved to Supabase for {ticker}")
            return response.data[0]
        return None
        
    except Exception as e:
        logger.error(f"Error saving analysis to Supabase: {e}")
        raise


def get_latest_analysis(ticker: str) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent analysis for a given ticker from Supabase."""
    try:
        client = get_supabase_client()
        
        response = (
            client.table("analysis_cache")
            .select("*")
            .eq("ticker", ticker.upper())
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            row = response.data[0]
            return {
                'id': row['id'],
                'ticker': row['ticker'],
                'analysis_summary': row['analysis_summary'],
                'sentiment_report': row['sentiment_report'],
                'price_data': row.get('price_data', []),
                'headlines': row.get('headlines', []),
                'reasoning_steps': row.get('reasoning_steps', []),
                'tools_used': row.get('tools_used', []),
                'iterations': row.get('iterations', 0),
                'timestamp': row.get('created_at'),
                # Structured sentiment
                'overall_sentiment': row.get('overall_sentiment', ''),
                'overall_confidence': row.get('overall_confidence', 0.0),
                'confidence_reasoning': row.get('confidence_reasoning', ''),
                'headline_analyses': row.get('headline_analyses', []),
                'key_themes': row.get('key_themes', []),
                'potential_impact': row.get('potential_impact', ''),
                'risks_identified': row.get('risks_identified', []),
                'information_gaps': row.get('information_gaps', []),
                # Skeptic analysis
                'skeptic_report': row.get('skeptic_report', ''),
                'skeptic_sentiment': row.get('skeptic_sentiment', ''),
                'skeptic_confidence': row.get('skeptic_confidence', 0.0),
                'primary_disagreement': row.get('primary_disagreement', ''),
                'critiques': row.get('critiques', []),
                'bear_cases': row.get('bear_cases', []),
                'hidden_risks': row.get('hidden_risks', []),
                'would_change_mind': row.get('would_change_mind', []),
                # Fundamentals
                'fundamental_data': row.get('fundamental_data', {}),
            }
        return None
        
    except Exception as e:
        logger.error(f"Error getting latest analysis from Supabase: {e}")
        return None


def delete_cached_analysis(ticker: str) -> bool:
    """Delete all cached analyses for a given ticker. Returns True if any were deleted."""
    try:
        client = get_supabase_client()
        
        response = (
            client.table("analysis_cache")
            .delete()
            .eq("ticker", ticker.upper())
            .execute()
        )
        
        deleted_count = len(response.data) if response.data else 0
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} cached analyses for {ticker}")
        return deleted_count > 0
        
    except Exception as e:
        logger.error(f"Error deleting cached analysis from Supabase: {e}")
        return False


def get_all_cached_tickers() -> List[str]:
    """Get a list of all unique tickers that have cached analysis data."""
    try:
        client = get_supabase_client()
        
        # Get distinct tickers - Supabase doesn't have DISTINCT, so we fetch and dedupe
        response = (
            client.table("analysis_cache")
            .select("ticker")
            .order("created_at", desc=True)
            .execute()
        )
        
        if response.data:
            # Deduplicate while preserving order (most recent first)
            seen = set()
            unique_tickers = []
            for row in response.data:
                ticker = row['ticker']
                if ticker not in seen:
                    seen.add(ticker)
                    unique_tickers.append(ticker)
            return unique_tickers
        return []
        
    except Exception as e:
        logger.error(f"Error getting all cached tickers from Supabase: {e}")
        return []


def get_all_cached_tickers_with_timestamps() -> List[Dict[str, Any]]:
    """
    Get a list of all tickers with their most recent analysis timestamps.
    Returns list of dicts with 'symbol' and 'timestamp' keys.
    """
    try:
        client = get_supabase_client()
        
        # Fetch all analyses ordered by time
        response = (
            client.table("analysis_cache")
            .select("ticker, created_at")
            .order("created_at", desc=True)
            .execute()
        )
        
        if response.data:
            # Get most recent timestamp for each ticker
            ticker_timestamps = {}
            for row in response.data:
                ticker = row['ticker']
                if ticker not in ticker_timestamps:
                    ticker_timestamps[ticker] = row['created_at']
            
            # Convert to list format
            return [
                {"symbol": ticker, "timestamp": timestamp}
                for ticker, timestamp in ticker_timestamps.items()
            ]
        return []
        
    except Exception as e:
        logger.error(f"Error getting cached tickers with timestamps from Supabase: {e}")
        return []


if __name__ == '__main__':
    # Test the Supabase connection
    init_db()
    
    sample_ticker = "TEST"
    sample_summary = "Test analysis summary."
    sample_sentiment = "Overall sentiment: Positive."
    
    print("Saving test analysis...")
    save_analysis(sample_ticker, sample_summary, sample_sentiment)
    
    print("Retrieving test analysis...")
    retrieved_data = get_latest_analysis(sample_ticker)
    print(f"Retrieved data: {retrieved_data}")
    
    print("Getting all cached tickers...")
    cached_tickers = get_all_cached_tickers()
    print(f"Cached tickers: {cached_tickers}")
    
    print("Getting cached tickers with timestamps...")
    cached_with_ts = get_all_cached_tickers_with_timestamps()
    print(f"Cached tickers with timestamps: {cached_with_ts}")
    
    print("Cleaning up test data...")
    delete_cached_analysis(sample_ticker)
    print("Done!")