"""
FastAPI main application for StockSense ReAct Agent API.

This module creates the REST API endpoints that expose the StockSense ReAct Agent
functionality through HTTP requests, allowing clients to request stock analysis
and retrieve cached results using the ReAct pattern.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any
from datetime import datetime

from .config import validate_configuration, ConfigurationError
from .database import init_db, get_latest_analysis, get_all_cached_tickers
from .react_agent import run_react_analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting StockSense ReAct Agent API...")
    
    try:
        print("Validating configuration...")
        validate_configuration()
        print("Configuration validation successful")
    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        raise
    
    print("Initializing database...")
    try:
        init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise
    
    print("StockSense ReAct Agent API ready to serve requests!")
    
    yield
    
    # Shutdown
    print("Shutting down StockSense ReAct Agent API...")


app = FastAPI(
    title="StockSense ReAct Agent API",
    description="AI-powered autonomous stock analysis using ReAct pattern",
    version="2.0.0",
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
        "message": "Welcome to StockSense ReAct Agent API",
        "description": "AI-powered autonomous stock analysis using ReAct pattern",
        "docs": "/docs",
        "health": "/health"
    }


@app.post("/analyze/{ticker}")
async def analyze_stock(ticker: str) -> Dict[str, Any]:
    """
    Analyze sentiment for a stock ticker using ReAct Agent.
    
    This endpoint uses the ReAct (Reasoning + Acting) pattern agent to perform
    autonomous stock analysis. The agent reasons about market conditions and
    dynamically selects appropriate tools for comprehensive analysis.
    
    Args:
        ticker (str): Stock ticker symbol (e.g., 'AAPL', 'NVDA')
        
    Returns:
        Dict[str, Any]: Analysis results from the ReAct agent
        
    Raises:
        HTTPException: If the analysis fails or invalid ticker is provided
    """
    try:
        # Validate and normalize ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")
        
        print(f"ReAct Agent analysis request received for ticker: {ticker}")
        
        # Check for cached analysis first
        print(f"Checking cache for existing analysis of {ticker}...")
        cached_analysis = get_latest_analysis(ticker)
        
        if cached_analysis:
            print(f"Found cached analysis for {ticker}")
            return {
                "message": "Analysis retrieved from cache",
                "ticker": ticker,
                "data": {
                    "id": cached_analysis["id"],
                    "ticker": cached_analysis["ticker"],
                    "summary": cached_analysis["analysis_summary"],
                    "sentiment_report": cached_analysis["sentiment_report"],
                    "timestamp": cached_analysis["timestamp"],
                    "source": "cache",
                    "agent_type": "ReAct"
                }
            }
        
        # No cached data found, run fresh ReAct analysis
        print(f"No cached data found for {ticker}, running fresh ReAct analysis...")
        
        # Run the ReAct agent
        try:
            final_state = run_react_analysis(ticker)
            
            # Check if the ReAct agent completed successfully
            if final_state.get("error"):
                error_msg = final_state["error"]
                print(f"ReAct Agent error for {ticker}: {error_msg}")
                raise HTTPException(
                    status_code=500, 
                    detail=f"ReAct Agent analysis failed: {error_msg}"
                )
            
            # Check if we have valid results
            summary = final_state.get("summary", "")
            sentiment_report = final_state.get("sentiment_report", "")
            
            if (not summary or summary.startswith("Analysis failed") or
                not sentiment_report or sentiment_report.startswith("Error")):
                raise HTTPException(
                    status_code=500,
                    detail="ReAct Agent completed but produced insufficient data"
                )
            
            # Save the analysis results to database
            try:
                from .database import save_analysis
                save_analysis(ticker, summary, sentiment_report)
                print(f"Analysis results saved to database for {ticker}")
            except Exception as e:
                print(f"Warning: Failed to save analysis to database: {str(e)}")
                # Don't fail the request if database save fails
            
            print(f"ReAct Agent analysis completed successfully for {ticker}")
            
            return {
                "message": "ReAct Agent analysis complete and saved",
                "ticker": ticker,
                "data": {
                    "ticker": final_state["ticker"],
                    "summary": final_state["summary"],
                    "sentiment_report": final_state["sentiment_report"],
                    "headlines_count": len(final_state.get("headlines", [])),
                    "reasoning_steps": final_state.get("reasoning_steps", []),
                    "tools_used": final_state.get("tools_used", []),
                    "iterations": final_state.get("iterations", 0),
                    "timestamp": final_state.get("timestamp"),
                    "source": "react_analysis",
                    "agent_type": "ReAct"
                }
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            error_msg = f"ReAct Agent execution error: {str(e)}"
            print(f"{error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        error_msg = f"Unexpected error analyzing {ticker}: {str(e)}"
        print(f"{error_msg}")
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
        
        print(f"Results request for ticker: {ticker}")
        
        # Get the latest analysis from database
        analysis = get_latest_analysis(ticker)
        
        if not analysis:
            print(f"No analysis found for {ticker}")
            raise HTTPException(
                status_code=404, 
                detail=f"No analysis found for ticker: {ticker}"
            )
        
        print(f"Analysis results retrieved for {ticker}")
        
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
        print(f"{error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/cached-tickers")
async def get_cached_tickers() -> Dict[str, Any]:
    """
    Get a list of all tickers that have cached analysis results.
    
    Returns:
        Dict[str, Any]: List of cached tickers with their timestamps
    """
    try:
        print("Retrieving list of cached tickers...")
        
        cached_tickers = get_all_cached_tickers()
        
        print(f"Found {len(cached_tickers)} cached tickers")
        
        return {
            "message": "Cached tickers retrieved successfully",
            "count": len(cached_tickers),
            "tickers": cached_tickers
        }
        
    except Exception as e:
        error_msg = f"Error retrieving cached tickers: {str(e)}"
        print(f"{error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


# Development server runner
if __name__ == "__main__":
    print("Starting StockSense ReAct Agent FastAPI development server...")
    uvicorn.run(
        "stocksense.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
