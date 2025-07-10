"""
FastAPI main application for StockSense Agent.

This module creates the REST API endpoints that expose the StockSense Agent
functionality through HTTP requests, allowing clients to request stock analysis
and retrieve cached results.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Dict, Any

# Import our modules
from .database import init_db, get_latest_analysis
from .workflow import app_workflow, run_analysis

# Create FastAPI application
app = FastAPI(
    title="StockSense Agent API",
    description="AI-powered stock market sentiment analysis API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Startup event handler to initialize the database.
    
    This function runs once when the FastAPI application starts up,
    ensuring that the database and required tables are properly initialized.
    """
    print("🚀 Starting StockSense Agent API...")
    print("📊 Initializing database...")
    
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        raise
    
    print("🎯 StockSense Agent API ready to serve requests!")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.
    
    Returns:
        Dict[str, str]: Status message indicating the API is operational
    """
    return {"status": "ok"}


@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic API information.
    
    Returns:
        Dict[str, str]: Welcome message and API information
    """
    return {
        "message": "Welcome to StockSense Agent API",
        "description": "AI-powered stock market sentiment analysis",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/analyze/{ticker}")
async def analyze_stock(ticker: str) -> Dict[str, Any]:
    """
    Analyze sentiment for a stock ticker.
    
    This endpoint first checks for cached analysis results. If none are found,
    it runs the complete analysis workflow including data collection, sentiment
    analysis, summarization, and database storage.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        
    Returns:
        Dict[str, Any]: Analysis results or cache retrieval confirmation
        
    Raises:
        HTTPException: If the analysis fails or invalid ticker is provided
    """
    try:
        # Validate and normalize ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")
        
        print(f"📈 Analysis request received for ticker: {ticker}")
        
        # Check for cached analysis first
        print(f"🔍 Checking cache for existing analysis of {ticker}...")
        cached_analysis = get_latest_analysis(ticker)
        
        if cached_analysis:
            print(f"💾 Found cached analysis for {ticker}")
            return {
                "message": "Analysis retrieved from cache",
                "ticker": ticker,
                "data": {
                    "id": cached_analysis["id"],
                    "ticker": cached_analysis["ticker"],
                    "summary": cached_analysis["analysis_summary"],
                    "sentiment_report": cached_analysis["sentiment_report"],
                    "timestamp": cached_analysis["timestamp"],
                    "source": "cache"
                }
            }
        
        # No cached data found, run fresh analysis
        print(f"🆕 No cached data found for {ticker}, running fresh analysis...")
        
        # Run the LangGraph workflow
        try:
            final_state = run_analysis(ticker)
            
            # Check if the workflow completed successfully
            if final_state.get("error"):
                error_msg = final_state["error"]
                print(f"❌ Workflow error for {ticker}: {error_msg}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"Analysis failed: {error_msg}"
                )
            
            # Check if we have valid results
            summary = final_state.get("summary", "")
            sentiment_report = final_state.get("sentiment_report", "")
            
            if (not summary or summary.startswith("Error") or summary.startswith("No summary") or
                not sentiment_report or sentiment_report.startswith("Error") or sentiment_report.startswith("No sentiment")):
                raise HTTPException(
                    status_code=500,
                    detail="Analysis completed but produced insufficient data"
                )
            
            print(f"✅ Analysis completed successfully for {ticker}")
            
            return {
                "message": "Analysis complete and saved",
                "ticker": ticker,
                "data": {
                    "ticker": final_state["ticker"],
                    "summary": final_state["summary"],
                    "sentiment_report": final_state["sentiment_report"],
                    "headlines_count": len(final_state.get("headlines", [])),
                    "source": "fresh_analysis"
                }
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            error_msg = f"Workflow execution error: {str(e)}"
            print(f"❌ {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Unexpected error analyzing {ticker}: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/results/{ticker}")
async def get_analysis_results(ticker: str) -> Dict[str, Any]:
    """
    Retrieve the latest analysis results for a stock ticker.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        
    Returns:
        Dict[str, Any]: Latest analysis results from the database
        
    Raises:
        HTTPException: If no analysis is found for the ticker
    """
    try:
        # Validate and normalize ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")
        
        print(f"📊 Results request for ticker: {ticker}")
        
        # Get the latest analysis from database
        analysis = get_latest_analysis(ticker)
        
        if not analysis:
            print(f"❌ No analysis found for {ticker}")
            raise HTTPException(
                status_code=404, 
                detail=f"No analysis found for ticker: {ticker}"
            )
        
        print(f"✅ Analysis results retrieved for {ticker}")
        
        return {
            "message": "Analysis results retrieved successfully",
            "ticker": ticker,
            "data": {
                "id": analysis["id"],
                "ticker": analysis["ticker"],
                "summary": analysis["analysis_summary"],
                "sentiment_report": analysis["sentiment_report"],
                "timestamp": analysis["timestamp"]
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Error retrieving results for {ticker}: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/cached-tickers")
async def get_cached_tickers() -> Dict[str, Any]:
    """
    Get a list of all tickers that have cached analysis results.
    
    Returns:
        Dict[str, Any]: List of cached tickers with their timestamps
    """
    try:
        print("📋 Retrieving list of cached tickers...")
        
        # Import here to avoid circular imports
        from .database import get_all_cached_tickers
        
        cached_tickers = get_all_cached_tickers()
        
        print(f"✅ Found {len(cached_tickers)} cached tickers")
        
        return {
            "message": "Cached tickers retrieved successfully",
            "count": len(cached_tickers),
            "tickers": cached_tickers
        }
        
    except Exception as e:
        error_msg = f"Error retrieving cached tickers: {str(e)}"
        print(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


# Development server runner
if __name__ == "__main__":
    print("🔧 Starting FastAPI development server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
