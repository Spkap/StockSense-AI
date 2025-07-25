"""
ReAct Agent implementation for StockSense using LangGraph built-in utilities.

This module implements a true ReAct (Reasoning + Acting) pattern agent that can:
- Reason about market conditions and data quality
- Dynamically select appropriate tools
- Adapt behavior based on observations
- Self-correct and iterate when needed
"""

import os
from typing import Dict, List, Optional, TypedDict, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

# Import our modules
from .config import get_chat_llm, ConfigurationError
from .data_collectors import get_news, get_price_history
from .analyzer import analyze_sentiment_of_headlines
from .database import save_analysis


class AgentState(TypedDict):
    """
    Enhanced state for ReAct agent with message history and tool tracking.
    """
    messages: List[BaseMessage]
    ticker: str
    headlines: List[str]
    price_data: Optional[Dict]
    sentiment_report: str
    summary: str
    reasoning_steps: List[str]
    tools_used: List[str]
    iterations: int
    max_iterations: int
    final_decision: str
    error: Optional[str]


# Define available tools using LangChain's @tool decorator
@tool
def fetch_news_headlines(ticker: str, days: int = 7) -> Dict:
    """
    Fetch recent news headlines for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol
        days: Number of days to look back for news
        
    Returns:
        Dictionary with headlines and metadata
    """
    try:
        headlines = get_news(ticker, days=days)
        return {
            "success": True,
            "headlines": headlines,
            "count": len(headlines),
            "ticker": ticker,
            "days": days
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "headlines": [],
            "count": 0
        }


@tool
def fetch_price_data(ticker: str, period: str = "1mo") -> Dict:
    """
    Fetch price history for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
    Returns:
        Dictionary with price data and metadata
    """
    try:
        price_data = get_price_history(ticker, period=period)
        return {
            "success": True,
            "price_data": price_data,
            "ticker": ticker,
            "period": period,
            "has_data": price_data is not None
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "price_data": None
        }


@tool
def analyze_sentiment(headlines: List[str]) -> Dict:
    """
    Analyze sentiment of news headlines.
    
    Args:
        headlines: List of news headlines
        
    Returns:
        Dictionary with sentiment analysis results
    """
    try:
        if not headlines:
            return {
                "success": False,
                "error": "No headlines provided for analysis",
                "sentiment_report": ""
            }
        
        sentiment_report = analyze_sentiment_of_headlines(headlines)
        return {
            "success": True,
            "sentiment_report": sentiment_report,
            "headlines_count": len(headlines)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sentiment_report": ""
        }


@tool
def save_analysis_results(ticker: str, summary: str, sentiment_report: str) -> Dict:
    """
    Save analysis results to database.
    
    Args:
        ticker: Stock ticker symbol
        summary: Analysis summary
        sentiment_report: Detailed sentiment report
        
    Returns:
        Dictionary with save operation results
    """
    try:
        save_analysis(ticker, summary, sentiment_report)
        return {
            "success": True,
            "message": f"Analysis saved for {ticker}",
            "ticker": ticker
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to save analysis for {ticker}"
        }


# Available tools
tools = [
    fetch_news_headlines,
    fetch_price_data,
    analyze_sentiment,
    save_analysis_results
]


def create_react_agent() -> StateGraph:
    """
    Create a ReAct agent using LangGraph built-in utilities and features.
    
    Returns:
        StateGraph: Configured ReAct agent ready for compilation
    """
    
    # Get configured Chat LLM instance for ReAct agent
    llm = get_chat_llm(
        model="gemini-1.5-flash",
        temperature=0.1,
        max_output_tokens=1024
    )
    
    # Bind tools to the LLM using LangGraph's built-in tool binding
    llm_with_tools = llm.bind_tools(tools)
    
    def agent_node(state: AgentState) -> AgentState:
        """
        Main agent reasoning node using ReAct pattern.
        """
        messages = state["messages"]
        ticker = state["ticker"]
        iterations = state.get("iterations", 0)
        max_iterations = state.get("max_iterations", 5)
        
        # Check iteration limit
        if iterations >= max_iterations:
            return {
                **state,
                "final_decision": "MAX_ITERATIONS_REACHED",
                "error": f"Reached maximum iterations ({max_iterations})"
            }
        
        # Create reasoning prompt based on current state
        reasoning_prompt = f"""
You are a ReAct (Reasoning + Acting) agent for stock analysis. You must analyze {ticker} by reasoning about what to do next and then taking action.

Current situation:
- Ticker: {ticker}
- Iteration: {iterations + 1}/{max_iterations}
- Headlines collected: {len(state.get('headlines', []))}
- Price data available: {state.get('price_data') is not None}
- Sentiment analyzed: {bool(state.get('sentiment_report'))}
- Tools used so far: {state.get('tools_used', [])}

Available tools:
1. fetch_news_headlines - Get recent news headlines
2. fetch_price_data - Get price history data
3. analyze_sentiment - Analyze sentiment of headlines
4. save_analysis_results - Save final analysis

REASONING: Think step by step about what you should do next:
1. What information do I have?
2. What information do I still need?
3. What tool should I use next?
4. Am I ready to provide a final analysis?

ACTION: Based on your reasoning, either:
- Use a tool to gather more information
- Provide a final summary if you have enough data

Be adaptive and intelligent about your approach. Consider market conditions, data quality, and completeness.
"""
        
        # Add the reasoning prompt to messages
        messages.append(HumanMessage(content=reasoning_prompt))
        
        # Get LLM response with tool calls
        response = llm_with_tools.invoke(messages)
        
        # Update state with new iteration
        new_state = {
            **state,
            "messages": messages + [response],
            "iterations": iterations + 1
        }
        
        # Check if the agent wants to use tools
        if response.tool_calls:
            new_state["final_decision"] = "CONTINUE"
        else:
            # Agent provided final answer
            new_state["final_decision"] = "COMPLETE"
            new_state["summary"] = response.content
        
        return new_state
    
    def custom_tool_node(state: AgentState) -> AgentState:
        """
        Tool execution node with state tracking.
        """
        messages = state["messages"]
        last_message = messages[-1]
        
        tool_results = []
        tools_used = state.get("tools_used", [])
        reasoning_steps = state.get("reasoning_steps", [])
        
        # Execute each tool call
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Find the tool function
            tool_function = None
            for tool in tools:
                if tool.name == tool_name:
                    tool_function = tool
                    break
            
            if tool_function:
                # Execute tool directly
                result = tool_function.invoke(tool_args)
            else:
                result = {"error": f"Tool {tool_name} not found"}
            
            # Create tool message
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )
            
            tool_results.append(tool_message)
            tools_used.append(tool_name)
            
            # Update state based on tool results
            if tool_name == "fetch_news_headlines" and result.get("success"):
                state["headlines"] = result.get("headlines", [])
                reasoning_steps.append(f"Fetched {len(state['headlines'])} headlines")
            
            elif tool_name == "fetch_price_data" and result.get("success"):
                state["price_data"] = result.get("price_data")
                reasoning_steps.append("Fetched price data")
            
            elif tool_name == "analyze_sentiment" and result.get("success"):
                state["sentiment_report"] = result.get("sentiment_report", "")
                reasoning_steps.append("Completed sentiment analysis")
            
            elif tool_name == "save_analysis_results" and result.get("success"):
                reasoning_steps.append("Saved analysis to database")
        
        # Update state with tool results
        return {
            **state,
            "messages": messages + tool_results,
            "tools_used": tools_used,
            "reasoning_steps": reasoning_steps
        }
        return {
            **state,
            "messages": messages + tool_results,
            "tools_used": tools_used,
            "reasoning_steps": reasoning_steps
        }
    
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """
        Conditional edge to determine if agent should continue or end.
        """
        final_decision = state.get("final_decision")
        
        if final_decision == "CONTINUE":
            return "tools"
        elif final_decision in ["COMPLETE", "MAX_ITERATIONS_REACHED"]:
            return "end"
        else:
            # Default to continue if no decision made
            return "tools"
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", custom_tool_node)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow


# Create and compile the ReAct agent
print("Initializing StockSense ReAct Agent...")
react_workflow = create_react_agent()
react_app = react_workflow.compile()
print("ReAct Agent ready!")


def run_react_analysis(ticker: str) -> Dict:
    """
    Run the ReAct agent analysis for a stock ticker.
    
    Args:
        ticker: Stock ticker symbol to analyze
        
    Returns:
        Dict: Final analysis results
    """
    print(f"\n{'='*60}")
    print(f"Starting ReAct Agent analysis for {ticker.upper()}")
    print(f"{'='*60}")
    
    # Initialize state
    initial_state = {
        "messages": [],
        "ticker": ticker.upper(),
        "headlines": [],
        "price_data": None,
        "sentiment_report": "",
        "summary": "",
        "reasoning_steps": [],
        "tools_used": [],
        "iterations": 0,
        "max_iterations": 5,
        "final_decision": "",
        "error": None
    }
    
    try:
        # Run the ReAct agent
        final_state = react_app.invoke(initial_state)
        
        print(f"\n{'='*60}")
        print(f"ReAct Agent completed analysis for {ticker.upper()}")
        print(f"Iterations used: {final_state.get('iterations', 0)}")
        print(f"Tools used: {final_state.get('tools_used', [])}")
        print(f"Reasoning steps: {len(final_state.get('reasoning_steps', []))}")
        print(f"{'='*60}")
        
        # Extract final results
        return {
            "ticker": final_state["ticker"],
            "summary": final_state.get("summary", "Analysis completed"),
            "sentiment_report": final_state.get("sentiment_report", ""),
            "headlines": final_state.get("headlines", []),
            "price_data": final_state.get("price_data"),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            "tools_used": final_state.get("tools_used", []),
            "iterations": final_state.get("iterations", 0),
            "error": final_state.get("error"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"ReAct Agent error for {ticker}: {str(e)}"
        print(f"{error_msg}")
        return {
            "ticker": ticker.upper(),
            "summary": "Analysis failed",
            "sentiment_report": "",
            "headlines": [],
            "price_data": None,
            "reasoning_steps": [],
            "tools_used": [],
            "iterations": 0,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == '__main__':
    """
    Test the ReAct agent with a sample ticker.
    """
    print(" Testing StockSense ReAct Agent")
    print("="*50)
    
    # Test ticker
    test_ticker = "AAPL"
    
    # Run the ReAct agent
    result = run_react_analysis(test_ticker)
    
    # Display results
    print(f"\n Final Results for {test_ticker}:")
    print("-" * 40)
    print(f"Ticker: {result['ticker']}")
    print(f"Headlines found: {len(result['headlines'])}")
    print(f"Tools used: {result['tools_used']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Error: {result.get('error', 'None')}")
    
    if result['summary']:
        print(f"\nSummary:\n{result['summary']}")
    
    if result['reasoning_steps']:
        print(f"\nReasoning Steps:")
        for i, step in enumerate(result['reasoning_steps'], 1):
            print(f"  {i}. {step}")
    
    print(f"\n ReAct Agent test completed!")
