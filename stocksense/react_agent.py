from typing import Dict, List, Optional, TypedDict, Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from .config import get_chat_llm
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


tools = [
    fetch_news_headlines,
    fetch_price_data,
    analyze_sentiment,
    save_analysis_results
]


def create_react_agent() -> StateGraph:

    llm = get_chat_llm(
        model="gemini-1.5-flash",
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
            return {
                **state,
                "final_decision": "MAX_ITERATIONS_REACHED",
                "error": f"Reached maximum iterations ({max_iterations})"
            }

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

COMPLETION CRITERIA: You are ready to provide final analysis when you have:
- Headlines collected (✓ if {len(state.get('headlines', []))} > 0)
- Price data gathered (✓ if {state.get('price_data') is not None})
- Sentiment analysis completed (✓ if {bool(state.get('sentiment_report'))})

ACTION: Based on your reasoning:
- If ANY of the above criteria are missing, use the appropriate tool to gather that information
- If ALL criteria are met, provide a comprehensive final summary WITHOUT calling any more tools
- DO NOT call analyze_sentiment more than once unless the first attempt failed

IMPORTANT: Once you have collected headlines, performed sentiment analysis, and gathered price data, provide a comprehensive final summary that includes:
- Overall market sentiment conclusion
- Key insights from the news analysis
- Market implications and investment considerations.
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
            new_state["final_decision"] = "COMPLETE"

            agent_response = response.content

            headlines = state.get('headlines', [])
            sentiment_report = state.get('sentiment_report', '')
            price_data = state.get('price_data')

            if sentiment_report and headlines:
                comprehensive_summary = f"""
Stock Analysis Summary for {ticker}:

Market Sentiment: Based on analysis of {len(headlines)} recent news headlines, the overall market sentiment shows {sentiment_report[:200]}...

Key Findings:
- News Coverage: {len(headlines)} articles analyzed from the past 7 days
- Price Data: {'Available' if price_data is not None else 'Not available'}
- Agent Reasoning: {agent_response}

The ReAct agent completed analysis using {len(set(state.get('tools_used', [])))} different tools across {iterations + 1} reasoning iterations.
                """.strip()

                new_state["summary"] = comprehensive_summary

                if sentiment_report and not any('save_analysis_results' in tool for tool in state.get('tools_used', [])):
                    print(f"Warning: ReAct agent didn't call save_analysis_results for {ticker}")
            else:
                new_state["summary"] = agent_response or f"Analysis completed for {ticker} but insufficient data collected"

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

            # Prevent redundant tool calls
            if tool_name == "analyze_sentiment" and state.get("sentiment_report"):
                result = {
                    "success": True,
                    "sentiment_report": state.get("sentiment_report"),
                    "message": "Sentiment analysis already completed"
                }
            elif tool_name == "fetch_news_headlines" and state.get("headlines"):
                result = {
                    "success": True,
                    "headlines": state.get("headlines"),
                    "message": "Headlines already fetched"
                }
            elif tool_name == "fetch_price_data" and state.get("price_data"):
                result = {
                    "success": True,
                    "price_data": state.get("price_data"),
                    "message": "Price data already fetched"
                }
            else:
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
        "max_iterations": 8,
        "final_decision": "",
        "error": None
    }

    try:
        # Run the ReAct agent
        final_state = react_app.invoke(initial_state)

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

        # Check if it's a rate limit error and provide helpful message
        if "429" in str(e) or "quota" in str(e).lower() or "rate" in str(e).lower():
            friendly_error = f"API Rate Limit Reached: Google Gemini free tier allows 50 requests/day. Please wait for quota reset or upgrade to paid plan."
            error_msg = friendly_error

        return {
            "ticker": ticker.upper(),
            "summary": f"Analysis temporarily unavailable due to API limits. The data collection was successful (found real market data), but AI analysis is rate-limited.",
            "sentiment_report": f"Rate Limit Info: Google Gemini free tier quota exceeded. Try again tomorrow or upgrade for higher limits.",
            "headlines": [],
            "price_data": None,
            "reasoning_steps": [],
            "tools_used": [],
            "iterations": 0,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == '__main__':
    test_ticker = "AAPL"
    result = run_react_analysis(test_ticker)