from fastapi import FastAPI, HTTPException, BackgroundTasks
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
    return {"status": "ok"}


@app.get("/")
async def root() -> Dict[str, str]:
    return {
        "message": "Welcome to StockSense ReAct Agent API",
        "description": "AI-powered autonomous stock analysis using ReAct pattern",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/analyze/{ticker}")
async def analyze_stock(ticker: str, background_tasks: BackgroundTasks) -> Dict[str, Any]: # <--- ADD BackgroundTasks ARGUMENT
    """
    Triggers a ReAct Agent analysis in the background for a given stock ticker.
    Checks the cache first and returns immediately if a result is found.
    """
    try:
        # Validate and normalize ticker
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")

        print(f"Analysis request received for ticker: {ticker}")

        # --- Step 1: Check cache ---
        print(f"Checking cache for existing analysis of {ticker}...")
        cached_analysis = get_latest_analysis(ticker)

        if cached_analysis:
            print(f"Found cached analysis for {ticker}")
            # The structure of this response should match the one in get_analysis_results
            # so the frontend can handle it consistently.
            cached_analysis['source'] = 'cache'
            cached_analysis['agent_type'] = 'ReAct'
            return {
                "message": "Analysis retrieved from cache",
                "ticker": ticker,
                "data": cached_analysis
            }

        # --- Step 2: If no cache, start analysis in the background ---
        print(f"No cached data for {ticker}. Starting analysis in the background...")
        
        # This is the key change: the long-running task is handed off.
        background_tasks.add_task(run_react_analysis, ticker)

        # --- Step 3: Return an immediate response ---
        # This tells the frontend that the job has started successfully.
        # The frontend will now poll the /results/{ticker} endpoint.
        return {
            "message": "Analysis has been started in the background",
            "ticker": ticker
        }

    except HTTPException:
        # Re-raise known HTTP exceptions
        raise
    except Exception as e:
        # Catch any other unexpected errors
        error_msg = f"Unexpected error in analysis request for {ticker}: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/results/{ticker}")
async def get_analysis_results(ticker: str) -> Dict[str, Any]:
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


if __name__ == "__main__":
    print("Starting StockSense ReAct Agent FastAPI development server...")
    uvicorn.run(
        "stocksense.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )