"""
StockSense ReAct Agent API
AI-powered autonomous stock analysis using ReAct pattern
"""
import json
import logging
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from .config import validate_configuration, ConfigurationError, get_google_api_key, get_newsapi_key
from .database import init_db, get_latest_analysis, get_all_cached_tickers_with_timestamps, delete_cached_analysis
from .react_agent import run_react_analysis
from .validation import validate_ticker

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("stocksense.api")


# Simple in-memory rate limiter
class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for given client."""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id] 
            if req_time > minute_ago
        ]
        
        # Check limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Record request
        self.requests[client_id].append(now)
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        now = time.time()
        minute_ago = now - 60
        recent = [r for r in self.requests[client_id] if r > minute_ago]
        return max(0, self.requests_per_minute - len(recent))


# Initialize rate limiter (10 analysis requests per minute per IP)
rate_limiter = RateLimiter(requests_per_minute=10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting StockSense ReAct Agent API...")

    try:
        logger.info("Validating configuration...")
        validate_configuration()
        logger.info("Configuration validation successful")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise

    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

    # Initialize Scheduler (Stage 5 Phase 2: The Watchman)
    try:
        from .scheduler import start_scheduler
        start_scheduler()
        logger.info("Background scheduler initialized")
    except Exception as e:
        logger.warning(f"Failed to start background scheduler: {e}")

    logger.info("StockSense ReAct Agent API ready to serve requests!")

    yield

    # Shutdown
    logger.info("Shutting down StockSense ReAct Agent API...")


app = FastAPI(
    title="StockSense ReAct Agent API",
    description="AI-powered autonomous stock analysis using ReAct pattern",
    version="3.0.0",  # Stage 3: User Belief System
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register auth routes (Stage 3: User Belief System)
try:
    from .auth_routes import router as auth_router
    app.include_router(auth_router)
    logger.info("Auth routes registered successfully")
except ImportError as e:
    logger.warning(f"Auth routes not available: {e}")


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Enhanced health check with dependency status.
    Returns detailed health information for monitoring.
    """
    health_status = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.1.0",
        "checks": {}
    }
    
    # Check Google API key
    try:
        get_google_api_key()
        health_status["checks"]["google_api_key"] = {"status": "ok"}
    except ConfigurationError as e:
        health_status["checks"]["google_api_key"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check NewsAPI key
    try:
        get_newsapi_key()
        health_status["checks"]["newsapi_key"] = {"status": "ok"}
    except ConfigurationError as e:
        health_status["checks"]["newsapi_key"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check database
    try:
        from .database import get_all_cached_tickers_with_timestamps
        tickers = get_all_cached_tickers_with_timestamps()
        health_status["checks"]["database"] = {
            "status": "ok",
            "cached_analyses": len(tickers)
        }
    except Exception as e:
        health_status["checks"]["database"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    return health_status


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with API information."""
    return {
        "message": "Welcome to StockSense ReAct Agent API",
        "description": "AI-powered autonomous stock analysis using ReAct pattern",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/analyze/{ticker}")
async def analyze_stock(
    ticker: str, 
    request: Request, 
    force: bool = False,
    authorization: str = None
) -> Dict[str, Any]:
    """
    Analyze stock using the ReAct Agent (Reasoning + Action) pattern.
    
    Args:
        ticker: Stock ticker symbol
        force: If True, bypass cache and run fresh analysis
        authorization: Optional Bearer token for authenticated features (kill criteria alerts)
    
    Includes ticker validation and rate limiting.
    """
    # Rate limiting
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(client_ip):
        remaining = rate_limiter.get_remaining(client_ip)
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded. Please wait before making more requests. Remaining: {remaining}"
        )
    
    try:
        # Validate ticker format and existence
        ticker = ticker.upper().strip()
        is_valid, error_msg = validate_ticker(ticker)
        if not is_valid:
            logger.info(f"Invalid ticker rejected: {ticker} - {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        logger.info(f"Analysis request received for ticker: {ticker} from {client_ip} (force={force})")

        # Check for cached analysis first (unless force=True)
        if not force:
            logger.debug(f"Checking cache for existing analysis of {ticker}...")
            cached_analysis = get_latest_analysis(ticker)

            if cached_analysis:
                logger.info(f"Found cached analysis for {ticker}")
                
                # Calculate cache age
                cache_age_hours = None
                if cached_analysis.get("timestamp"):
                    try:
                        cached_time = datetime.fromisoformat(cached_analysis["timestamp"])
                        age_seconds = (datetime.utcnow() - cached_time).total_seconds()
                        cache_age_hours = round(age_seconds / 3600, 1)
                    except (ValueError, TypeError):
                        pass
                
                return {
                    "message": "Analysis retrieved from cache",
                    "ticker": ticker,
                    "data": {
                        "id": cached_analysis["id"],
                        "ticker": cached_analysis["ticker"],
                        "summary": cached_analysis["analysis_summary"],
                        "sentiment_report": cached_analysis["sentiment_report"],
                        "timestamp": cached_analysis["timestamp"],
                        "cache_age_hours": cache_age_hours,
                        "source": "cache",
                        "agent_type": "ReAct",
                        "price_data": cached_analysis.get("price_data", []),
                        "headlines": cached_analysis.get("headlines", []),
                        "headlines_count": len(cached_analysis.get("headlines", [])),
                        "reasoning_steps": cached_analysis.get("reasoning_steps", []),
                        "tools_used": cached_analysis.get("tools_used", []),
                        "iterations": cached_analysis.get("iterations", 0)
                    }
                }
        else:
            logger.info(f"Force refresh requested for {ticker}, skipping cache")

        # No cached data found or force=True, run fresh ReAct analysis
        logger.info(f"Running fresh ReAct analysis for {ticker}...")

        # Run the ReAct agent
        try:
            final_state = run_react_analysis(ticker)

            # Check if the ReAct agent completed successfully
            if final_state.get("error"):
                error_msg = final_state["error"]
                logger.error(f"ReAct Agent error for {ticker}: {error_msg}")
                raise HTTPException(
                    status_code=500,
                    detail=f"ReAct Agent analysis failed: {error_msg}"
                )

            # Check if we have valid results
            summary = final_state.get("summary", "")
            sentiment_report = final_state.get("sentiment_report", "")

            if not summary or summary.startswith("Analysis failed"):
                raise HTTPException(
                    status_code=500,
                    detail="ReAct Agent completed but produced insufficient data"
                )

            # Save the analysis results to database with full data
            try:
                from .database import save_analysis
                save_analysis(
                    ticker=ticker,
                    summary=summary,
                    sentiment_report=sentiment_report,
                    price_data=final_state.get("price_data", []),
                    headlines=final_state.get("headlines", []),
                    reasoning_steps=final_state.get("reasoning_steps", []),
                    tools_used=final_state.get("tools_used", []),
                    iterations=final_state.get("iterations", 0)
                )
                logger.info(f"Analysis results saved to database for {ticker}")
            except Exception as e:
                logger.warning(f"Failed to save analysis to database: {str(e)}")
                # Don't fail the request if database save fails

            logger.info(f"ReAct Agent analysis completed successfully for {ticker}")

            # Stage 4: Kill Criteria Monitoring
            # Check if user is authenticated and run kill criteria check
            kill_alerts_created = []
            if authorization:
                try:
                    from .supabase_client import verify_user_token
                    from .kill_criteria_monitor import check_kill_criteria_for_ticker
                    
                    # Parse Bearer token
                    parts = authorization.split(" ")
                    if len(parts) == 2 and parts[0].lower() == "bearer":
                        access_token = parts[1]
                        user = verify_user_token(access_token)
                        
                        if user:
                            logger.info(f"Running kill criteria check for user {user['id']} on {ticker}")
                            kill_alerts_created = check_kill_criteria_for_ticker(
                                ticker=ticker,
                                analysis_result=final_state,
                                user_id=user["id"],
                                access_token=access_token
                            )
                            if kill_alerts_created:
                                logger.info(f"Created {len(kill_alerts_created)} kill alerts for {ticker}")
                except Exception as e:
                    logger.warning(f"Kill criteria check failed (non-fatal): {e}")

            return {
                "message": "ReAct Agent analysis complete and saved",
                "ticker": ticker,
                "kill_alerts": kill_alerts_created,  # Stage 4: Include triggered alerts
                "data": {
                    "ticker": final_state["ticker"],
                    "summary": final_state["summary"],
                    "sentiment_report": final_state["sentiment_report"],
                    "price_data": final_state.get("price_data", []),
                    "headlines": final_state.get("headlines", []),
                    "headlines_count": len(final_state.get("headlines", [])),
                    "reasoning_steps": final_state.get("reasoning_steps", []),
                    "tools_used": final_state.get("tools_used", []),
                    "iterations": final_state.get("iterations", 0),
                    "timestamp": final_state.get("timestamp"),
                    "cache_age_hours": 0,  # Fresh analysis
                    "source": "react_analysis",
                    "agent_type": "ReAct",
                    # Stage 1: Structured sentiment fields
                    "overall_sentiment": final_state.get("overall_sentiment", ""),
                    "overall_confidence": final_state.get("overall_confidence", 0.0),
                    "confidence_reasoning": final_state.get("confidence_reasoning", ""),
                    "headline_analyses": final_state.get("headline_analyses", []),
                    "key_themes": final_state.get("key_themes", []),
                    "potential_impact": final_state.get("potential_impact", ""),
                    "risks_identified": final_state.get("risks_identified", []),
                    "information_gaps": final_state.get("information_gaps", []),
                    # Stage 2: Skeptic analysis fields
                    "skeptic_report": final_state.get("skeptic_report", ""),
                    "skeptic_sentiment": final_state.get("skeptic_sentiment", ""),
                    "skeptic_confidence": final_state.get("skeptic_confidence", 0.0),
                    "primary_disagreement": final_state.get("primary_disagreement", ""),
                    "critiques": final_state.get("critiques", []),
                    "bear_cases": final_state.get("bear_cases", []),
                    "hidden_risks": final_state.get("hidden_risks", []),
                    "would_change_mind": final_state.get("would_change_mind", [])
                }
            }

        except HTTPException:
            raise
        except Exception as e:
            error_msg = f"ReAct Agent execution error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise HTTPException(status_code=500, detail=error_msg)

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error analyzing {ticker}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/results/{ticker}")
async def get_analysis_results(ticker: str) -> Dict[str, Any]:
    """Get cached analysis results for a ticker."""
    try:
        # Validate ticker format
        ticker = ticker.upper().strip()
        is_valid, error_msg = validate_ticker(ticker, check_exists=False)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        logger.debug(f"Results request for ticker: {ticker}")

        # Get the latest analysis from database
        analysis = get_latest_analysis(ticker)

        if not analysis:
            logger.debug(f"No analysis found for {ticker}")
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for ticker: {ticker}"
            )

        logger.debug(f"Analysis results retrieved for {ticker}")

        return {
            "message": "Analysis results retrieved successfully",
            "ticker": ticker,
            "data": {
                "id": analysis["id"],
                "ticker": analysis["ticker"],
                "summary": analysis["analysis_summary"],
                "sentiment_report": analysis["sentiment_report"],
                "price_data": analysis.get("price_data", []),
                "headlines": analysis.get("headlines", []),
                "headlines_count": len(analysis.get("headlines", [])),
                "reasoning_steps": analysis.get("reasoning_steps", []),
                "tools_used": analysis.get("tools_used", []),
                "iterations": analysis.get("iterations", 0),
                "timestamp": analysis["timestamp"],
                "source": "cache",
                "agent_type": "ReAct"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error retrieving results for {ticker}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.delete("/results/{ticker}")
async def delete_analysis_results(ticker: str) -> Dict[str, str]:
    """Delete cached analysis results for a ticker."""
    try:
        # Validate ticker format
        ticker = ticker.upper().strip()
        is_valid, error_msg = validate_ticker(ticker, check_exists=False)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        logger.info(f"Delete request for ticker: {ticker}")

        deleted = delete_cached_analysis(ticker)

        if not deleted:
            raise HTTPException(
                status_code=404,
                detail=f"No analysis found for ticker: {ticker}"
            )

        logger.info(f"Analysis deleted for {ticker}")
        return {
            "message": f"Analysis for {ticker} deleted successfully",
            "ticker": ticker
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Error deleting analysis for {ticker}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/cached-tickers")
async def get_cached_tickers() -> Dict[str, Any]:
    """
    Get list of cached tickers with timestamps.
    Returns ticker symbols and when they were analyzed.
    """
    try:
        logger.debug("Retrieving list of cached tickers...")

        cached_tickers = get_all_cached_tickers_with_timestamps()

        logger.debug(f"Found {len(cached_tickers)} cached tickers")

        return {
            "message": "Cached tickers retrieved successfully",
            "count": len(cached_tickers),
            "tickers": cached_tickers
        }

    except Exception as e:
        error_msg = f"Error retrieving cached tickers: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/analyze/{ticker}/stream")
async def analyze_stock_stream(ticker: str, request: Request):
    """
    Stream analysis using Server-Sent Events (SSE).
    
    Stage 4: Streaming Analysis with Progressive Rendering
    
    Yields events as each tool completes:
    - started: Analysis initiated
    - tool_started: Starting a specific tool
    - tool_completed: Tool finished with partial data
    - completed: Full analysis result
    - error: If something goes wrong
    """
    from .streaming import run_streaming_analysis
    
    # Rate limiting
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(client_ip):
        async def error_response():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Rate limit exceeded'})}\n\n"
        return StreamingResponse(
            error_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    # Validate ticker
    ticker = ticker.upper().strip()
    is_valid, error_msg = validate_ticker(ticker)
    if not is_valid:
        async def error_response():
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
        return StreamingResponse(
            error_response(),
            media_type="text/event-stream"
        )
    
    logger.info(f"Streaming analysis request for {ticker} from {client_ip}")
    
    async def event_generator():
        """Generate SSE events from streaming analysis."""
        import json
        
        try:
            async for event in run_streaming_analysis(ticker):
                yield event.to_sse()
                
                # If completed, also save to cache
                if event.event_type.value == "completed" and event.data:
                    try:
                        from .database import save_analysis
                        save_analysis(
                            ticker=ticker,
                            summary=event.data.get("summary", ""),
                            sentiment_report=event.data.get("sentiment_report", ""),
                            price_data=event.data.get("price_data", []),
                            headlines=event.data.get("headlines", []),
                            reasoning_steps=[],
                            tools_used=event.data.get("tools_used", []),
                            iterations=1
                        )
                        logger.info(f"Streaming analysis saved to cache for {ticker}")
                    except Exception as e:
                        logger.warning(f"Failed to save streaming analysis: {e}")
                        
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


if __name__ == "__main__":
    # Support Render / other PaaS dynamic port assignment
    port = int(os.getenv("PORT", "8000"))
    reload_flag = os.getenv("UVICORN_RELOAD", "false").lower() == "true"
    log_level = os.getenv("LOG_LEVEL", "info")
    logger.info(f"Starting StockSense ReAct Agent FastAPI server on 0.0.0.0:{port} (reload={reload_flag}) ...")
    uvicorn.run(
        "stocksense.main:app",
        host="0.0.0.0",
        port=port,
        reload=reload_flag,
        log_level=log_level
    )