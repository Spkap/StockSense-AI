
import logging
import asyncio
from typing import List, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

# config imports removed - using supabase_client directly
from .supabase_client import get_supabase_client
from .react_agent import run_react_analysis
from .kill_criteria_monitor import extract_signals_from_analysis, match_signals_to_criteria, check_kill_criteria_for_ticker

logger = logging.getLogger("stocksense.scheduler")

scheduler = AsyncIOScheduler()

async def check_all_active_theses():
    """
    Background job: Fetch all active theses, analyze their tickers, and check kill criteria.
    """
    logger.info("Starting background thesis check...")
    
    try:
        client = get_supabase_client()
        
        # 1. Fetch all active theses with kill criteria
        # Note: In a real prod app, we'd paginate this or use a queue.
        # For now, we fetch all active theses.
        response = client.table("theses")\
            .select("id, user_id, ticker, kill_criteria")\
            .eq("status", "active")\
            .not_.is_("kill_criteria", "null")\
            .execute()
        
        theses = response.data
        if not theses:
            logger.info("No active theses to check.")
            return

        # 2. Group by ticker to avoid redundant analysis
        # Map: ticker -> list of (user_id, thesis_id)
        ticker_map: Dict[str, List[Dict[str, str]]] = {}
        for thesis in theses:
            ticker = thesis["ticker"]
            if ticker not in ticker_map:
                ticker_map[ticker] = []
            ticker_map[ticker].append({
                "user_id": thesis["user_id"],
                "thesis_id": thesis["id"]
            })
        
        logger.info(f"Checking {len(ticker_map)} unique tickers for {len(theses)} theses.")

        # 3. Analyze each ticker
        for ticker, users in ticker_map.items():
            try:
                logger.info(f"Analyzing {ticker}...")
                
                # Run the full agent analysis (Phase 1 updated version with fundamentals)
                # This is a synchronous function effectively (calls LLM), so we run it directly.
                # In a heavy load, we might offload this to a thread pool executor.
                analysis_result = await asyncio.to_thread(run_react_analysis, ticker)
                
                # 4. Check kill criteria for each user interested in this ticker
                # We need to act on behalf of each user. 
                # Ideally, we'd have a system user or service role. 
                # For now, we'll re-use the logic but we need an access token.
                # LIMITATION: The current 'check_kill_criteria_for_ticker' expects a user token.
                # We will need to adapt it or create a 'service_role' version.
                # For this implementation, we will assume we can write alerts directly using the service key client
                # (which get_supabase_client returns if configured with service key, but typically it uses anon).
                
                # Let's manually implement the alert saving for the background job 
                # to avoid auth complexity of "acting as user".
                
                signals = extract_signals_from_analysis(
                    summary=analysis_result.get("summary", ""),
                    sentiment_report=analysis_result.get("sentiment_report", ""),
                    key_themes=analysis_result.get("key_themes", []),
                    risks_identified=analysis_result.get("risks_identified", []),
                    bear_cases=analysis_result.get("bear_cases", []),
                    hidden_risks=analysis_result.get("hidden_risks", [])
                )
                
                if not signals:
                    continue

                for user_info in users:
                    # Get this specific thesis to check its criteria
                    # (We could optimize by passing criteria from step 1, but let's be safe)
                    thesis_row = next((t for t in theses if t["id"] == user_info["thesis_id"]), None)
                    if not thesis_row: 
                        continue
                        
                    kill_criteria = thesis_row.get("kill_criteria", [])
                    if not kill_criteria:
                        continue

                    matches = match_signals_to_criteria(signals, kill_criteria, ticker)
                    
                    for match in matches:
                        if match.match_confidence >= 0.6:
                            # Create Alert directly in alert_history (Phase 2)
                            message = f"Kill Criteria Triggered: {match.criteria}"
                            
                            data_json = {
                                "triggered_criteria": match.criteria,
                                "triggering_signal": match.signal,
                                "match_confidence": match.match_confidence,
                                "analysis_sentiment": analysis_result.get("overall_sentiment", ""),
                                "analysis_confidence": analysis_result.get("overall_confidence", 0.0),
                                "analysis_summary": analysis_result.get("summary", "")[:500],
                                "status": "pending",
                                "source": "background_monitor"
                            }
                            
                            alert_data = {
                                "user_id": user_info["user_id"],
                                "thesis_id": user_info["thesis_id"],
                                "ticker": ticker,
                                "alert_type": "kill_criteria",
                                "message": message,
                                "data": data_json,
                                "is_read": False
                            }
                            
                            try:
                                client.table("alert_history").insert(alert_data).execute()
                                logger.info(f"Background Alert Created: {ticker} for user {user_info['user_id']}")
                            except Exception as e:
                                logger.error(f"Failed to save background alert: {e}")

            except Exception as e:
                logger.error(f"Error processing {ticker} in background job: {e}")
                
    except Exception as e:
        logger.error(f"Critical error in check_all_active_theses: {e}")

def start_scheduler():
    """Start the background scheduler."""
    # Run every hour
    scheduler.add_job(check_all_active_theses, IntervalTrigger(hours=1), id='thesis_check', replace_existing=True)
    scheduler.start()
    logger.info("Background scheduler started.")
