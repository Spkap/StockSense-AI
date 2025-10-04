import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import Dict, Any

# Add the parent directory to Python path to enable imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from core.config import validate_configuration, ConfigurationError
from ai.react_agent import run_react_analysis


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

    print("StockSense ReAct Agent API ready to serve requests!")

    yield

    # Shutdown
    print("Shutting down StockSense ReAct Agent API...")


app = FastAPI(
    title="StockSense AI Analysis API",
    description="AI-powered stock analysis with data sources",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint with API information."""
    return {
        "message": "StockSense AI Analysis API",
    }


@app.get("/analyze/{ticker}")
async def analyze_stock(ticker: str) -> Dict[str, Any]:
    """
    Comprehensive stock analysis endpoint.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
        
    Returns:
        Complete analysis with data and sources
    """
    try:
        # Validate ticker input
        ticker = ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker symbol is required")
        
        if not ticker.replace('.', '').replace('-', '').isalpha() or len(ticker) > 10:
            raise HTTPException(status_code=400, detail="Invalid ticker format")

        print(f"Starting analysis for ticker: {ticker}")

        analysis_result = run_react_analysis(ticker)
        print(f"Raw analysis result: {analysis_result}")

        # Check for errors
        if analysis_result.get("error"):
            error_msg = analysis_result["error"]
            if "rate" in error_msg.lower() or "429" in error_msg:
                raise HTTPException(
                    status_code=429, 
                    detail="API rate limit reached. Please try again later."
                )
            raise HTTPException(status_code=500, detail=f"Analysis failed: {error_msg}")

        # Extract analysis components
        summary = analysis_result.get("summary", "")
        sentiment_report = analysis_result.get("sentiment_report", "")
        headlines = analysis_result.get("headlines", [])
        price_data = analysis_result.get("price_data", [])
        reasoning_steps = analysis_result.get("reasoning_steps", [])
        tools_used = analysis_result.get("tools_used", [])
        final_decision = analysis_result.get("final_decision", "UNSPECIFIED")

        # Validate we have meaningful results
        if not summary or summary.startswith("Analysis failed"):
            raise HTTPException(
                status_code=500, 
                detail="Analysis completed but insufficient data generated"
            )


        return {
            "success": True,
            "ticker": ticker,
            "analysis": {
                "summary": summary,
                "sentiment_report": sentiment_report,
                "recommendation": final_decision,
                "confidence": "high" if len(tools_used) >= 3 else "medium"
            },
            "data_sources": {
                "news_headlines": {
                    "count": len(headlines),
                    "headlines": headlines[:10],
                    "source": "NewsAPI"
                },
                "price_data": {
                    "data_points": len(price_data),
                    "latest_price": price_data[-1]["Close"] if price_data else None,
                    "price_range": {
                        "period": "30 days",
                        "high": max([p["High"] for p in price_data]) if price_data else None,
                        "low": min([p["Low"] for p in price_data]) if price_data else None
                    },
                    "source": "Yahoo Finance",
                    "chart_data": price_data 
                },
                "ai_analysis": {
                    "model": "Google Gemini 2.5 Flash",
                    "reasoning_steps": len(reasoning_steps),
                    "tools_used": tools_used,
                    "iterations": analysis_result.get("iterations", 0),
                    "sentiment_analyzed": analysis_result.get("sentiment_analyzed", False)
                }
            },
            "metadata": {
                "analysis_type": "ReAct Agent",
                "timestamp": analysis_result.get("timestamp"),
                "processing_time": f"{analysis_result.get('iterations', 0)} AI iterations",
                "data_freshness": "Real-time"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Unexpected error analyzing {ticker}: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail="Internal server error")


