import os
import sys

from typing import Dict, List, Optional, TypedDict, Literal, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

# Add the parent directories to Python path to find modules
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_dir = os.path.dirname(current_dir)
stocksense_dir = os.path.dirname(ai_dir)
sys.path.append(stocksense_dir)

from core.config import get_chat_llm
from data.collectors.data_collectors import get_news, get_price_history
from ai.analyzer import analyze_sentiment_of_headlines

class AgentState(TypedDict):
    """
    Enhanced state for ReAct agent with message history and tool tracking.
    """
    messages: List[BaseMessage]
    ticker: str
    headlines: List[Dict[str, str]] 
    price_data: List[Dict[str, Any]] 
    sentiment_report: str
    summary: str
    reasoning_steps: List[str]
    tools_used: List[str]
    iterations: int
    max_iterations: int
    final_decision: str
    error: Optional[str]


@tool
def fetch_news_headlines(ticker: str, days: int = 7) -> Dict:
    """
    Fetch recent news headlines for a stock ticker. 
    This is STEP 1 of the mandatory analysis workflow.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        days: Number of days to look back for news (default: 7)
    
    Returns:
        Dict with news data including headlines list and metadata
    """
    try:
        news_data = get_news(ticker, days=days)
        
        return {
            "success": True,
            "news": news_data,
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
    Fetch price history for a stock ticker and return structured OHLCV data.
    This is STEP 2 of the mandatory analysis workflow.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        period: Time period for price data (default: "1mo")
    
    Returns:
        Dict with price data including OHLCV values and metadata
    """
    try:
        df = get_price_history(ticker, period=period)
        
        if df is None or df.empty:
            return {
                "success": False,
                "error": "No price data available",
                "price_data": []
            }
        
        df_reset = df.reset_index()
        df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
        
        price_data = []
        for record in df_reset.to_dict(orient='records'):
            price_record = {
                'Date': record['Date'],
                'Open': float(record['Open']) if record['Open'] is not None else None,
                'High': float(record['High']) if record['High'] is not None else None,
                'Low': float(record['Low']) if record['Low'] is not None else None,
                'Close': float(record['Close']) if record['Close'] is not None else None,
                'Volume': int(record['Volume']) if record['Volume'] is not None else None
            }
            price_data.append(price_record)
        
        return {
            "success": True,
            "price_data": price_data,
            "ticker": ticker,
            "period": period,
            "data_points": len(price_data),
            "has_data": len(price_data) > 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "price_data": []
        }


@tool
def analyze_sentiment(ticker: str) -> Dict:
    """
    Analyze sentiment of recent news headlines for a stock ticker.
    This is STEP 3 of the mandatory analysis workflow - must be called AFTER steps 1 and 2.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
    
    Returns:
        Dict with sentiment analysis report and success status
    """
    try:
        # Fetch fresh headlines for sentiment analysis
        news_data = get_news(ticker, days=7)
        headlines = news_data if news_data else []
        
        if not headlines:
            return {
                "success": False,
                "error": f"No headlines found for {ticker} to analyze sentiment",
                "sentiment_report": "",
                "headlines_analyzed": 0
            }

        sentiment_report = analyze_sentiment_of_headlines(headlines)
        
        return {
            "success": True,
            "sentiment_report": sentiment_report,
            "headlines_analyzed": len(headlines),
            "ticker": ticker
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sentiment_report": "",
            "headlines_analyzed": 0
        }


tools = [
    fetch_news_headlines,
    fetch_price_data,
    analyze_sentiment
]


def create_react_agent() -> StateGraph:

    llm = get_chat_llm(
        model="gemini-2.5-flash",
        temperature=0.1,
        max_output_tokens=1024
    )

    llm_with_tools = llm.bind_tools(tools)

    def agent_node(state: AgentState) -> AgentState:
        """
        Main agent reasoning node using ReAct pattern.
        """
        messages = state["messages"]
        ticker = state["ticker"]
        iterations = state.get("iterations", 0)
        max_iterations = state.get("max_iterations", 5)

        if iterations >= max_iterations:
            # Generate fallback summary with available data if max iterations reached
            tools_used = state.get("tools_used", [])
            required_tools = ["fetch_news_headlines", "fetch_price_data", "analyze_sentiment"]
            missing_tools = [tool for tool in required_tools if tool not in tools_used]
            
            fallback_summary = f"""
Stock Analysis Summary for {ticker} (Partial - Max Iterations Reached):

Analysis Status: Incomplete due to iteration limit
Tools Used: {', '.join(tools_used) if tools_used else 'None'}
Missing Tools: {', '.join(missing_tools) if missing_tools else 'None'}

Available Data Summary:
- News Headlines: {'✓' if 'fetch_news_headlines' in tools_used else '✗'} 
- Price Data: {'✓' if 'fetch_price_data' in tools_used else '✗'}
- Sentiment Analysis: {'✓' if 'analyze_sentiment' in tools_used else '✗'}

Final Recommendation: UNSPECIFIED (Incomplete Analysis)

Note: Analysis was incomplete due to reaching maximum iteration limit ({max_iterations}).
Please retry for complete analysis.
            """.strip()
            
            return {
                **state,
                "final_decision": "MAX_ITERATIONS_REACHED",
                "summary": fallback_summary,
                "error": f"Reached maximum iterations ({max_iterations}) - partial analysis provided"
            }

        reasoning_prompt = f"""
You are a ReAct (Reasoning + Action) agent for stock analysis. You must analyze {ticker} following this EXACT sequence:

MANDATORY WORKFLOW:
1. FIRST: Call fetch_news_headlines("{ticker}") to get recent news
2. SECOND: Call fetch_price_data("{ticker}") to get price history  
3. THIRD: Call analyze_sentiment("{ticker}") to analyze news sentiment
4. FOURTH: Provide final analysis combining ALL data

IMPORTANT RULES:
- You MUST use ALL THREE tools before providing final analysis
- Each tool provides crucial data for comprehensive analysis
- Do NOT skip any tools - all are required
- After using all tools, provide your final analysis with:
  * Market sentiment from news analysis
  * Price trend insights from historical data
  * Key insights combining news + price data
  * Final Investment Recommendation: either KEEP (hold) or SELL

Be explicit: Always end with 'Final Recommendation: KEEP' or 'Final Recommendation: SELL'.

Start by calling the first tool: fetch_news_headlines("{ticker}")
"""

        messages.append(HumanMessage(content=reasoning_prompt))

        response = llm_with_tools.invoke(messages)

        new_state = {
            **state,
            "messages": messages + [response],
            "iterations": iterations + 1
        }

        if response.tool_calls:
            new_state["final_decision"] = "CONTINUE"
        else:
            # Check if all required tools have been used before final analysis
            tools_used = state.get("tools_used", [])
            required_tools = ["fetch_news_headlines", "fetch_price_data", "analyze_sentiment"]
            missing_tools = [tool for tool in required_tools if tool not in tools_used]
            
            if missing_tools:
                # If tools are missing, force continuation with specific instruction
                missing_tools_str = ", ".join(missing_tools)
                continuation_prompt = f"""
You have not completed all required analysis steps. You are missing: {missing_tools_str}

IMPORTANT: You MUST use all three tools before providing final analysis.
Please call the missing tools now: {missing_tools_str}

Do not provide final analysis until you have used ALL required tools:
1. fetch_news_headlines("{ticker}")
2. fetch_price_data("{ticker}")  
3. analyze_sentiment("{ticker}")
"""
                
                new_state["messages"].append(HumanMessage(content=continuation_prompt))
                new_state["final_decision"] = "CONTINUE"
                
            else:
                # All tools used, proceed with final analysis
                agent_response = response.content or ""
                decision = "KEEP" if "KEEP" in agent_response.upper() else "SELL" if "SELL" in agent_response.upper() else "UNSPECIFIED"
                new_state["final_decision"] = decision

                comprehensive_summary = f"""
Stock Analysis Summary for {ticker}:

{agent_response}

Final Recommendation: {decision}

Analysis completed using {len(set(tools_used))} tools across {iterations + 1} reasoning iterations.
                """.strip()

                new_state["summary"] = comprehensive_summary

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

        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            tool_function = None
            for tool_item in tools:
                if tool_item.name == tool_name:
                    tool_function = tool_item
                    break

            if tool_function:
                result = tool_function.invoke(tool_args)
            else:
                result = {"error": f"Tool {tool_name} not found"}

            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call["id"]
            )

            tool_results.append(tool_message)
            tools_used.append(tool_name)

            if tool_name == "fetch_news_headlines" and result.get("success"):
                state["headlines"] = result.get("news", [])
                reasoning_steps.append(f"Fetched {len(state['headlines'])} headlines")

            elif tool_name == "fetch_price_data" and result.get("success"):
                state["price_data"] = result.get("price_data", [])
                data_points = len(state["price_data"]) if state["price_data"] else 0
                reasoning_steps.append(f"Fetched price data with {data_points} data points")

            elif tool_name == "analyze_sentiment" and result.get("success"):
                state["sentiment_report"] = result.get("sentiment_report", "")
                reasoning_steps.append("Completed sentiment analysis")

        return {
            **state,
            "messages": messages + tool_results,
            "tools_used": tools_used,
            "reasoning_steps": reasoning_steps
        }

    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        final_decision = state.get("final_decision")
        if final_decision == "CONTINUE":
            return "tools"
        elif final_decision in ["COMPLETE", "MAX_ITERATIONS_REACHED", "KEEP", "SELL", "UNSPECIFIED"]:
            return "end"
        else:
            return "tools"

    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", custom_tool_node)

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


react_workflow = create_react_agent()
react_app = react_workflow.compile()


def run_react_analysis(ticker: str) -> Dict:
    initial_state = {
        "messages": [],
        "ticker": ticker.upper(),
        "headlines": [],
        "price_data": [],
        "sentiment_report": "",
        "summary": "",
        "reasoning_steps": [],
        "tools_used": [],
        "iterations": 0,
        "max_iterations": 8,
        "final_decision": "",
        "error": None
    }

    try:
        final_state = react_app.invoke(initial_state)

        return {
            "ticker": final_state["ticker"],
            "summary": final_state.get("summary", "Analysis completed"),
            "sentiment_report": final_state.get("sentiment_report", ""),
            "headlines": final_state.get("headlines", []),
            "price_data": final_state.get("price_data"),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            "tools_used": final_state.get("tools_used", []),
            "iterations": final_state.get("iterations", 0),
            "final_decision": final_state.get("final_decision", "UNSPECIFIED"), 
            "error": final_state.get("error"),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        error_msg = str(e)

        return {
            "ticker": ticker.upper(),
            "summary": "Analysis temporarily unavailable due to API limits.",
            "sentiment_report": "Rate Limit Info: Gemini free tier quota exceeded.",
            "headlines": [],
            "price_data": [],
            "reasoning_steps": [],
            "tools_used": [],
            "iterations": 0,
            "final_decision": "UNSPECIFIED",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }

