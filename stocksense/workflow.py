"""
LangGraph workflow module for StockSense Agent.

This module defines a stateful graph that orchestrates the entire stock analysis process
using LangGraph to manage the workflow from data collection to database storage.
"""

import os
from typing import Dict, List, Optional, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import GoogleGenerativeAI

# Import our modules
from .data_collectors import get_news
from .analyzer import analyze_sentiment_of_headlines  
from .database import save_analysis

# Load environment variables
load_dotenv()


class AgentState(TypedDict):
    """
    State definition for the StockSense Agent workflow.
    
    This TypedDict defines the state that flows through the entire graph,
    tracking the ticker, collected data, analysis results, and any errors.
    """
    ticker: str
    headlines: List[str]
    sentiment_report: str
    summary: str
    error: Optional[str]


def fetch_data_node(state: AgentState) -> AgentState:
    """
    Node function to fetch news data for the given ticker.
    
    Args:
        state (AgentState): Current state containing the ticker
        
    Returns:
        AgentState: Updated state with headlines or error information
    """
    try:
        ticker = state["ticker"]
        print(f"📰 Fetching news data for {ticker}...")
        
        # Fetch news headlines using the data collector
        headlines = get_news(ticker, days=7)
        
        if not headlines:
            error_msg = f"No news headlines found for ticker {ticker}"
            print(f"⚠️  Warning: {error_msg}")
            return {
                **state,
                "headlines": [],
                "error": error_msg
            }
        
        print(f"✅ Successfully fetched {len(headlines)} headlines for {ticker}")
        return {
            **state,
            "headlines": headlines,
            "error": None
        }
        
    except Exception as e:
        error_msg = f"Error fetching data for {state['ticker']}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "headlines": [],
            "error": error_msg
        }


def analyze_sentiment_node(state: AgentState) -> AgentState:
    """
    Node function to analyze sentiment of the collected headlines.
    
    Args:
        state (AgentState): Current state containing headlines
        
    Returns:
        AgentState: Updated state with sentiment analysis report
    """
    try:
        headlines = state["headlines"]
        ticker = state["ticker"]
        
        # Skip analysis if no headlines or previous error
        if state.get("error") or not headlines:
            print(f"⏭️  Skipping sentiment analysis for {ticker} due to previous error or no headlines")
            return {
                **state,
                "sentiment_report": "No sentiment analysis performed - insufficient data"
            }
        
        print(f"🤖 Analyzing sentiment for {ticker} headlines...")
        
        # Perform sentiment analysis using the analyzer
        sentiment_report = analyze_sentiment_of_headlines(headlines)
        
        print(f"✅ Sentiment analysis completed for {ticker}")
        return {
            **state,
            "sentiment_report": sentiment_report
        }
        
    except Exception as e:
        error_msg = f"Error analyzing sentiment for {state['ticker']}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "sentiment_report": f"Error during sentiment analysis: {str(e)}",
            "error": error_msg
        }


def summarize_node(state: AgentState) -> AgentState:
    """
    Node function to create a brief summary based on the sentiment analysis.
    
    Args:
        state (AgentState): Current state containing sentiment report
        
    Returns:
        AgentState: Updated state with summary
    """
    try:
        sentiment_report = state["sentiment_report"]
        ticker = state["ticker"]
        
        # Skip summarization if no sentiment report or previous error
        if state.get("error") or not sentiment_report or sentiment_report.startswith("Error") or sentiment_report.startswith("No sentiment"):
            print(f"⏭️  Skipping summarization for {ticker} due to previous error or insufficient data")
            return {
                **state,
                "summary": "No summary available - insufficient data for analysis"
            }
        
        print(f"📝 Creating summary for {ticker}...")
        
        # Get Google API key
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            error_msg = "Google API key not found for summarization"
            print(f"❌ {error_msg}")
            return {
                **state,
                "summary": "Error: Could not create summary - API key missing",
                "error": error_msg
            }
        
        # Initialize the LLM for summarization
        llm = GoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.3,
            max_output_tokens=512
        )
        
        # Create summarization prompt
        prompt = f"""
Based on the following detailed sentiment analysis for {ticker}, please create a brief, professional summary in 2-3 sentences that captures:
1. The overall market sentiment (positive/negative/neutral)
2. The key factor(s) driving this sentiment
3. The potential impact on the stock

Sentiment Analysis Report:
{sentiment_report}

Please provide only the summary, without any additional formatting or explanations.
"""
        
        # Generate summary
        summary = llm.invoke(prompt)
        
        print(f"✅ Summary created for {ticker}")
        return {
            **state,
            "summary": summary.strip()
        }
        
    except Exception as e:
        error_msg = f"Error creating summary for {state['ticker']}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "summary": f"Error creating summary: {str(e)}",
            "error": error_msg
        }


def save_to_db_node(state: AgentState) -> AgentState:
    """
    Node function to save the analysis results to the database.
    
    Args:
        state (AgentState): Current state containing all analysis results
        
    Returns:
        AgentState: Final state with save confirmation
    """
    try:
        ticker = state["ticker"]
        summary = state["summary"]
        sentiment_report = state["sentiment_report"]
        
        # Only save if we have meaningful data
        if (not state.get("error") and 
            summary and not summary.startswith("Error") and not summary.startswith("No summary") and
            sentiment_report and not sentiment_report.startswith("Error") and not sentiment_report.startswith("No sentiment")):
            
            print(f"💾 Saving analysis results for {ticker} to database...")
            
            # Save to database
            save_analysis(ticker, summary, sentiment_report)
            
            print(f"✅ Analysis results saved for {ticker}")
        else:
            print(f"⏭️  Skipping database save for {ticker} - insufficient or invalid data")
        
        return state
        
    except Exception as e:
        error_msg = f"Error saving to database for {state['ticker']}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **state,
            "error": error_msg
        }


# Build the LangGraph workflow
def create_workflow() -> StateGraph:
    """
    Create and configure the StockSense Agent workflow graph.
    
    Returns:
        StateGraph: Configured workflow graph ready for compilation
    """
    print("🔧 Building StockSense Agent workflow...")
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("fetch_data", fetch_data_node)
    workflow.add_node("analyze_sentiment", analyze_sentiment_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("save_to_db", save_to_db_node)
    
    # Define the flow edges
    workflow.add_edge("fetch_data", "analyze_sentiment")
    workflow.add_edge("analyze_sentiment", "summarize")
    workflow.add_edge("summarize", "save_to_db")
    workflow.add_edge("save_to_db", END)
    
    # Set entry point
    workflow.set_entry_point("fetch_data")
    
    print("✅ Workflow graph constructed successfully")
    return workflow


# Create and compile the workflow application
print("🚀 Initializing StockSense Agent workflow...")
workflow_graph = create_workflow()
app_workflow = workflow_graph.compile()
print("✅ Workflow application ready!")


def run_analysis(ticker: str) -> Dict:
    """
    Convenience function to run the complete analysis workflow for a ticker.
    
    Args:
        ticker (str): Stock ticker symbol to analyze
        
    Returns:
        Dict: Final state after running the complete workflow
    """
    print(f"\n{'='*60}")
    print(f"🎯 Starting StockSense analysis for {ticker.upper()}")
    print(f"{'='*60}")
    
    # Initialize state
    initial_state = {
        "ticker": ticker.upper(),
        "headlines": [],
        "sentiment_report": "",
        "summary": "",
        "error": None
    }
    
    try:
        # Run the workflow
        final_state = app_workflow.invoke(initial_state)
        
        print(f"\n{'='*60}")
        if final_state.get("error"):
            print(f"⚠️  Analysis completed with errors for {ticker.upper()}")
        else:
            print(f"🎉 Analysis completed successfully for {ticker.upper()}")
        print(f"{'='*60}")
        
        return final_state
        
    except Exception as e:
        error_msg = f"Workflow execution error for {ticker}: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            **initial_state,
            "error": error_msg
        }


if __name__ == '__main__':
    """
    Test the workflow with a sample ticker.
    """
    print("🧪 Testing StockSense Agent Workflow")
    print("="*50)
    
    # Test ticker
    test_ticker = "AAPL"
    
    # Run the workflow
    result = run_analysis(test_ticker)
    
    # Display results
    print(f"\n📊 Final Results for {test_ticker}:")
    print("-" * 40)
    print(f"Ticker: {result['ticker']}")
    print(f"Headlines found: {len(result['headlines'])}")
    print(f"Error: {result.get('error', 'None')}")
    
    if result['summary'] and not result['summary'].startswith('Error') and not result['summary'].startswith('No summary'):
        print(f"\nSummary:\n{result['summary']}")
    
    print(f"\n🏁 Workflow test completed!")
