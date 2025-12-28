from typing import Dict, List, Optional, TypedDict, Literal, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool

from stocksense.core.config import get_chat_llm
from stocksense.core.data_collectors import get_news, get_price_history, get_fundamental_data
from stocksense.core.analyzer import analyze_sentiment_of_headlines
from stocksense.db.database import save_analysis


class AgentState(TypedDict):
    """
    Enhanced state for ReAct agent with message history and tool tracking.
    Includes structured sentiment analysis fields for epistemic transparency.
    """
    messages: List[BaseMessage]
    ticker: str
    headlines: List[str]
    price_data: List[Dict[str, Any]]
    fundamental_data: Dict[str, Any]  # New: Financial statements and metrics
    sentiment_report: str
    summary: str
    reasoning_steps: List[str]
    tools_used: List[str]
    iterations: int
    max_iterations: int
    final_decision: str
    error: Optional[str]
    # Structured sentiment analysis fields (Stage 1: Epistemic Foundation)
    overall_sentiment: str  # Bullish/Bearish/Neutral/Insufficient Data
    overall_confidence: float  # 0.0 to 1.0
    confidence_reasoning: str  # Explanation of confidence level
    headline_analyses: List[Dict[str, Any]]  # Per-headline breakdown
    key_themes: List[Dict[str, Any]]  # Recurring themes
    potential_impact: str  # Expected market impact
    risks_identified: List[str]  # Explicit risks
    information_gaps: List[str]  # What we don't know
    # Skeptic analysis fields (Stage 2: Visible Skepticism)
    skeptic_report: str  # Formatted skeptic analysis
    skeptic_sentiment: str  # Disagree/Partially Disagree/Agree with Reservations/Agree
    skeptic_confidence: float  # 0.0 to 1.0
    primary_disagreement: str  # Main point of contention
    critiques: List[Dict[str, Any]]  # Specific critiques
    bear_cases: List[Dict[str, Any]]  # Bear case scenarios
    hidden_risks: List[str]  # Risks not surfaced in primary
    would_change_mind: List[str]  # What would make skeptic bullish


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
        ticker = ticker.upper().strip()
        headlines = get_news(ticker, days=days)

        # Consider retrieval successful only if we have at least one headline.
        if headlines:
            return {
                "success": True,
                "headlines": headlines,
                "count": len(headlines),
                "ticker": ticker,
                "days": days
            }
        else:
            return {
                "success": False,
                "error": "No headlines found",
                "headlines": [],
                "count": 0,
                "ticker": ticker,
                "days": days
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "headlines": [],
            "count": 0,
            "ticker": ticker.upper().strip() if isinstance(ticker, str) else None,
            "days": days
        }


@tool
def fetch_price_data(ticker: str, period: str = "1mo") -> Dict:
    """
    Fetch price history for a stock ticker and return structured OHLCV data.

    Args:
        ticker: Stock ticker symbol
        period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)

    Returns:
        Dictionary with structured price data and metadata
    """
    try:
        ticker = ticker.upper().strip()
        df = get_price_history(ticker, period=period)

        if df is None or df.empty:
            return {
                "success": False,
                "error": "No price data available",
                "price_data": [],
                "ticker": ticker,
                "period": period,
                "data_points": 0,
                "has_data": False
            }
        
        # Convert DataFrame to list of dictionaries with structured OHLCV data
        df_reset = df.reset_index()
        df_reset['Date'] = df_reset['Date'].dt.strftime('%Y-%m-%d')
        
        # Convert to records and ensure proper data types
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
            "price_data": [],
            "ticker": ticker.upper().strip() if isinstance(ticker, str) else None,
            "period": period,
            "data_points": 0,
            "has_data": False
        }


@tool
def fetch_fundamentals(ticker: str) -> Dict:
    """
    Fetch fundamental financial data (Income Statement, Balance Sheet, Cash Flow, Key Ratios).
    Use this to verify quantitative claims (e.g. "revenue growth", "margins", "debt").

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with financial statements and info
    """
    try:
        ticker = ticker.upper().strip()
        data = get_fundamental_data(ticker)

        if not data or not data.get("info"):
            return {
                "success": False,
                "error": "No fundamental data available",
                "ticker": ticker
            }
        
        return {
            "success": True,
            "data": data,
            "ticker": ticker,
            "message": "Successfully fetched fundamental data"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "ticker": ticker
        }

@tool
def analyze_sentiment(headlines: List[str]) -> Dict:
    """
    Analyze sentiment of news headlines with structured output.

    Args:
        headlines: List of news headlines

    Returns:
        Dictionary with structured sentiment analysis including:
        - overall_sentiment: Bullish/Bearish/Neutral/Insufficient Data
        - overall_confidence: 0.0 to 1.0
        - headline_analyses: per-headline breakdown
        - key_themes: recurring themes identified
        - risks_identified: explicit risk factors
        - information_gaps: what we don't know
    """
    try:
        if not headlines:
            return {
                "success": False,
                "error": "No headlines provided for analysis",
                "sentiment_report": "",
                "structured_analysis": None
            }

        # Import structured analysis function
        from stocksense.core.analyzer import analyze_sentiment_structured, format_sentiment_result
        
        # Get structured result
        structured_result = analyze_sentiment_structured(headlines)
        
        # Format as readable report for backward compatibility
        sentiment_report = format_sentiment_result(structured_result)
        
        return {
            "success": True,
            "sentiment_report": sentiment_report,
            "headlines_count": len(headlines),
            # New structured fields
            "overall_sentiment": structured_result.overall_sentiment,
            "overall_confidence": structured_result.overall_confidence,
            "confidence_reasoning": structured_result.confidence_reasoning,
            "bullish_count": structured_result.bullish_count,
            "bearish_count": structured_result.bearish_count,
            "neutral_count": structured_result.neutral_count,
            "insufficient_data_count": structured_result.insufficient_data_count,
            "headline_analyses": [
                {
                    "headline": ha.headline,
                    "sentiment": ha.sentiment,
                    "confidence": ha.confidence,
                    "reasoning": ha.reasoning,
                    "key_entities": ha.key_entities
                }
                for ha in structured_result.headline_analyses
            ],
            "key_themes": [
                {
                    "theme": kt.theme,
                    "sentiment_direction": kt.sentiment_direction,
                    "headline_count": kt.headline_count,
                    "summary": kt.summary
                }
                for kt in structured_result.key_themes
            ],
            "potential_impact": structured_result.potential_impact,
            "risks_identified": structured_result.risks_identified,
            "information_gaps": structured_result.information_gaps
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "sentiment_report": "",
            "structured_analysis": None
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


@tool
def generate_skeptic_critique(ticker: str, headlines: List[str], primary_sentiment: str, primary_confidence: float) -> Dict:
    """
    Generate a skeptical critique of the primary analysis (Stage 2: Visible Skepticism).
    
    The Skeptic's job is to challenge conclusions, surface bear cases, and identify hidden risks.
    This should be called AFTER sentiment analysis completes.

    Args:
        ticker: Stock ticker symbol
        headlines: List of news headlines that were analyzed
        primary_sentiment: The primary analysis sentiment (Bullish/Bearish/Neutral)
        primary_confidence: The primary analysis confidence (0.0 to 1.0)

    Returns:
        Dictionary with skeptic analysis including critiques, bear cases, and hidden risks
    """
    try:
        from stocksense.agents.skeptic_agent import generate_skeptic_analysis, format_skeptic_analysis
        from stocksense.core.schemas import SentimentAnalysisResult
        
        # Create minimal primary analysis for skeptic to critique
        mock_primary = SentimentAnalysisResult(
            overall_sentiment=primary_sentiment,
            overall_confidence=primary_confidence,
            confidence_reasoning="Based on headline analysis",
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            insufficient_data_count=0,
            headline_analyses=[],
            key_themes=[],
            potential_impact="Uncertain",
            risks_identified=[],
            information_gaps=[]
        )
        
        skeptic_result = generate_skeptic_analysis(mock_primary, headlines, ticker)
        skeptic_report = format_skeptic_analysis(skeptic_result)
        
        return {
            "success": True,
            "skeptic_report": skeptic_report,
            "skeptic_sentiment": skeptic_result.skeptic_sentiment,
            "primary_disagreement": skeptic_result.primary_disagreement,
            "skeptic_confidence": skeptic_result.skeptic_confidence,
            "critiques": [
                {
                    "critique": c.critique,
                    "assumption_challenged": c.assumption_challenged,
                    "evidence": c.evidence
                }
                for c in skeptic_result.critiques
            ],
            "bear_cases": [
                {
                    "argument": b.argument,
                    "trigger": b.trigger,
                    "severity": b.severity
                }
                for b in skeptic_result.bear_cases
            ],
            "hidden_risks": skeptic_result.hidden_risks,
            "would_change_mind": skeptic_result.would_change_mind
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "skeptic_report": f"Skeptic analysis unavailable: {str(e)}"
        }


tools = [
    fetch_news_headlines,
    fetch_price_data,
    fetch_fundamentals,  # New tool
    analyze_sentiment,
    generate_skeptic_critique,
    save_analysis_results
]


def create_react_agent() -> StateGraph:

    llm = get_chat_llm(
        model="gemini-2.5-flash-lite",
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
You are a ReAct (Reasoning + Action) agent for stock analysis. You must analyze {ticker} by reasoning about what to do next and then taking action.

Current situation:
- Ticker: {ticker}
- Iteration: {iterations + 1}/{max_iterations}
- Headlines collected: {len(state.get('headlines', []))}
- Price data available: {len(state.get('price_data', [])) > 0}
- Fundamentals available: {bool(state.get('fundamental_data'))}
- Sentiment analyzed: {bool(state.get('sentiment_report'))}
- Skeptic critique done: {bool(state.get('skeptic_report'))}
- Tools used so far: {state.get('tools_used', [])}

Available tools:
1. fetch_news_headlines - Get recent news headlines
2. fetch_price_data - Get price history data
3. fetch_fundamentals - Get financial statements and key ratios (P/E, Revenue, Margins)
4. analyze_sentiment - Analyze sentiment of headlines (returns structured confidence)
5. generate_skeptic_critique - Challenge the primary analysis with bear cases and hidden risks
6. save_analysis_results - Save final analysis

REASONING: Think step by step about what you should do next:
1. What information do I have?
2. What information do I still need?
3. What tool should I use next?
4. Am I ready to provide a final analysis?

REQUIRED SEQUENCE:
1. First: fetch_news_headlines AND fetch_price_data (can be ANY order)
2. Then: fetch_fundamentals (Crucial for verifying kill criteria like 'Revenue slows down')
3. Then: analyze_sentiment (requires headlines)
4. Then: generate_skeptic_critique (requires sentiment - pass the overall_sentiment and overall_confidence from the sentiment result)
5. Finally: Provide comprehensive summary

COMPLETION CRITERIA: You are ready to provide final analysis when you have:
- Headlines collected (✓ if {len(state.get('headlines', []))} > 0)
- Price data gathered (✓ if {len(state.get('price_data', [])) > 0})
- Fundamentals gathered (✓ if {bool(state.get('fundamental_data'))})
- Sentiment analysis completed (✓ if {bool(state.get('sentiment_report'))})
- Skeptic critique generated (✓ if {bool(state.get('skeptic_report'))})

ACTION: Based on your reasoning:
- If ANY of the above criteria are missing, use the appropriate tool to gather that information
- If the stock is an ETF or Index (e.g. SPY, QQQ), fundamentals might fail - that's acceptable, just proceed.
- AFTER analyze_sentiment, you MUST call generate_skeptic_critique with the ticker, headlines, primary sentiment, and confidence
- If ALL criteria are met, provide a comprehensive final summary WITHOUT calling any more tools

IMPORTANT: Once you have ALL required data including the skeptic critique, provide a comprehensive final summary that includes:
- Overall market sentiment conclusion with confidence level
- Key insights from the news analysis
- Skeptic's perspective on the analysis
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
            price_data = state.get('price_data', [])
            fundamental_data = state.get('fundamental_data', {})

            if sentiment_report and headlines:
                comprehensive_summary = f"""
Stock Analysis Summary for {ticker}:

Market Sentiment: Based on analysis of {len(headlines)} recent news headlines, the overall market sentiment shows {sentiment_report[:200]}...

Key Findings:
- News Coverage: {len(headlines)} articles analyzed from the past 7 days
- Price Data: {'Available' if len(price_data) > 0 else 'Not available'} ({len(price_data)} data points)
- Fundamentals: {'Available' if fundamental_data else 'Not available'}
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
            elif tool_name == "fetch_fundamentals" and state.get("fundamental_data"):
                result = {
                    "success": True,
                    "data": state.get("fundamental_data"),
                    "message": "Fundamental data already fetched"
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
                state["price_data"] = result.get("price_data", [])
                data_points = len(state["price_data"]) if state["price_data"] else 0
                reasoning_steps.append(f"Fetched price data with {data_points} data points")

            elif tool_name == "fetch_fundamentals" and result.get("success"):
                state["fundamental_data"] = result.get("data", {})
                reasoning_steps.append("Fetched fundamental data (financials & ratios)")

            elif tool_name == "analyze_sentiment" and result.get("success"):
                state["sentiment_report"] = result.get("sentiment_report", "")
                # Store structured sentiment data (Stage 1: Epistemic Foundation)
                state["overall_sentiment"] = result.get("overall_sentiment", "")
                state["overall_confidence"] = result.get("overall_confidence", 0.0)
                state["confidence_reasoning"] = result.get("confidence_reasoning", "")
                state["headline_analyses"] = result.get("headline_analyses", [])
                state["key_themes"] = result.get("key_themes", [])
                state["potential_impact"] = result.get("potential_impact", "")
                state["risks_identified"] = result.get("risks_identified", [])
                state["information_gaps"] = result.get("information_gaps", [])
                reasoning_steps.append(f"Completed structured sentiment analysis (confidence: {state['overall_confidence']:.0%})")

            elif tool_name == "generate_skeptic_critique" and result.get("success"):
                # Store skeptic analysis data (Stage 2: Visible Skepticism)
                state["skeptic_report"] = result.get("skeptic_report", "")
                state["skeptic_sentiment"] = result.get("skeptic_sentiment", "")
                state["skeptic_confidence"] = result.get("skeptic_confidence", 0.0)
                state["primary_disagreement"] = result.get("primary_disagreement", "")
                state["critiques"] = result.get("critiques", [])
                state["bear_cases"] = result.get("bear_cases", [])
                state["hidden_risks"] = result.get("hidden_risks", [])
                state["would_change_mind"] = result.get("would_change_mind", [])
                reasoning_steps.append(f"Generated skeptic critique (verdict: {state['skeptic_sentiment']})")

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


_cached_react_app = None


def get_react_app():
    """Lazily create and compile the ReAct workflow app.

    This avoids constructing the LLM and binding tools at import time so unit
    tests that only require the tool functions (news/price fetchers) can import
    this module without needing Google API keys or the optional LLM dependency.
    """
    global _cached_react_app
    if _cached_react_app is None:
        workflow = create_react_agent()
        _cached_react_app = workflow.compile()
    return _cached_react_app


def run_react_analysis(ticker: str) -> Dict:
    # Initialize state with structured sentiment and skeptic fields
    initial_state = {
        "messages": [],
        "ticker": ticker.upper(),
        "headlines": [],
        "price_data": [],
        "fundamental_data": {},  # Init empty
        "sentiment_report": "",
        "summary": "",
        "reasoning_steps": [],
        "tools_used": [],
        "iterations": 0,
        "max_iterations": 10,  # Increased to accommodate skeptic analysis
        "final_decision": "",
        "error": None,
        # Structured sentiment fields (Stage 1)
        "overall_sentiment": "",
        "overall_confidence": 0.0,
        "confidence_reasoning": "",
        "headline_analyses": [],
        "key_themes": [],
        "potential_impact": "",
        "risks_identified": [],
        "information_gaps": [],
        # Skeptic analysis fields (Stage 2)
        "skeptic_report": "",
        "skeptic_sentiment": "",
        "skeptic_confidence": 0.0,
        "primary_disagreement": "",
        "critiques": [],
        "bear_cases": [],
        "hidden_risks": [],
        "would_change_mind": []
    }

    try:
        # Run the ReAct agent (create/compile lazily to avoid import-time LLM init)
        react_app = get_react_app()
        final_state = react_app.invoke(initial_state)

        # Extract final results with structured sentiment and skeptic data
        return {
            "ticker": final_state["ticker"],
            "summary": final_state.get("summary", "Analysis completed"),
            "sentiment_report": final_state.get("sentiment_report", ""),
            "headlines": final_state.get("headlines", []),
            "price_data": final_state.get("price_data"),
            "fundamental_data": final_state.get("fundamental_data"),
            "reasoning_steps": final_state.get("reasoning_steps", []),
            "tools_used": final_state.get("tools_used", []),
            "iterations": final_state.get("iterations", 0),
            "error": final_state.get("error"),
            "timestamp": datetime.now().isoformat(),
            # Structured sentiment analysis (Stage 1: Epistemic Foundation)
            "overall_sentiment": final_state.get("overall_sentiment", ""),
            "overall_confidence": final_state.get("overall_confidence", 0.0),
            "confidence_reasoning": final_state.get("confidence_reasoning", ""),
            "headline_analyses": final_state.get("headline_analyses", []),
            "key_themes": final_state.get("key_themes", []),
            "potential_impact": final_state.get("potential_impact", ""),
            "risks_identified": final_state.get("risks_identified", []),
            "information_gaps": final_state.get("information_gaps", []),
            # Skeptic analysis (Stage 2: Visible Skepticism)
            "skeptic_report": final_state.get("skeptic_report", ""),
            "skeptic_sentiment": final_state.get("skeptic_sentiment", ""),
            "skeptic_confidence": final_state.get("skeptic_confidence", 0.0),
            "primary_disagreement": final_state.get("primary_disagreement", ""),
            "critiques": final_state.get("critiques", []),
            "bear_cases": final_state.get("bear_cases", []),
            "hidden_risks": final_state.get("hidden_risks", []),
            "would_change_mind": final_state.get("would_change_mind", [])
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
            "price_data": [],  # Changed from None to empty list
            "fundamental_data": {},
            "reasoning_steps": [],
            "tools_used": [],
            "iterations": 0,
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }


if __name__ == '__main__':
    test_ticker = "AAPL"
    result = run_react_analysis(test_ticker)


# ============================================================================
# Phase 3: Adversarial Collaboration (Debate Analysis)
# ============================================================================

import asyncio
from stocksense.agents import BullAnalyst, BearAnalyst, Synthesizer, SynthesizedVerdict
from stocksense.core.analyzer import analyze_sentiment_structured


async def run_debate_analysis(ticker: str) -> Dict:
    """
    Run adversarial collaboration analysis with Bull and Bear agents.
    
    Architecture:
    1. Phase 1 (Parallel): Bull and Bear agents analyze data concurrently
    2. Phase 2 (Rebuttal): Each agent critiques the other's draft
    3. Phase 3 (Synthesis): Impartial judge synthesizes final verdict
    
    Returns a SynthesizedVerdict with probability-weighted scenarios.
    """
    import logging
    logger = logging.getLogger("stocksense.debate")
    
    ticker = ticker.upper()
    logger.info(f"Starting debate analysis for {ticker}")
    
    try:
        # Step 0: Collect data (shared by both agents)
        fundamentals = await asyncio.to_thread(get_fundamental_data, ticker)
        headlines = await asyncio.to_thread(get_news, ticker, 7)
        price_data = await asyncio.to_thread(get_price_history, ticker, "1mo")
        
        # Ensure fundamentals is a dict
        if fundamentals is None:
            fundamentals = {}
        
        # Analyze sentiment (shared context) - use structured version
        sentiment_analysis = {}
        if headlines:
            try:
                sentiment_result = await asyncio.to_thread(
                    analyze_sentiment_structured, headlines
                )
                # Convert Pydantic model to dict for agents
                sentiment_analysis = {
                    "overall_sentiment": sentiment_result.overall_sentiment,
                    "overall_confidence": sentiment_result.overall_confidence,
                    "key_themes": [
                        {
                            "theme": t.theme,
                            "sentiment_direction": t.sentiment_direction,
                            "headline_count": t.headline_count,
                            "summary": t.summary
                        }
                        for t in sentiment_result.key_themes
                    ],
                    "risks_identified": sentiment_result.risks_identified,
                    "potential_impact": sentiment_result.potential_impact
                }
            except Exception as e:
                logger.warning(f"Sentiment analysis failed: {e}")
                sentiment_analysis = {}
        
        # Step 1: Initialize agents
        bull_agent = BullAnalyst()
        bear_agent = BearAnalyst()
        synthesizer = Synthesizer()
        
        # Step 2: Phase 1 - Parallel initial analysis
        logger.info("Phase 1: Parallel Bull/Bear analysis")
        
        bull_task = bull_agent.analyze(
            ticker, fundamentals, headlines, price_data, sentiment_analysis
        )
        bear_task = bear_agent.analyze(
            ticker, fundamentals, headlines, price_data, sentiment_analysis
        )
        
        # Run in parallel - reduces latency by ~50%
        bull_case, bear_case = await asyncio.gather(bull_task, bear_task)
        
        # Convert to dicts for rebuttal phase
        bull_dict = bull_case.to_dict()
        bear_dict = bear_case.to_dict()
        
        logger.info(f"Bull confidence: {bull_case.confidence:.2f}, Bear confidence: {bear_case.confidence:.2f}")
        
        # Step 3: Phase 2 - Rebuttal Round (Anti-Sycophancy)
        logger.info("Phase 2: Rebuttal Round")
        
        # Bear critiques Bull
        bear_rebuttals = await bear_agent.generate_rebuttal(
            bull_dict, bear_dict, fundamentals
        )
        
        # Bull critiques Bear
        bull_rebuttals = await bull_agent.generate_rebuttal(
            bear_dict, bull_dict, fundamentals
        )
        
        # Convert rebuttals to dicts
        bear_rebuttals_dict = [
            {
                "target_claim": r.target_claim,
                "counter_argument": r.counter_argument,
                "counter_evidence": r.counter_evidence,
                "strength": r.strength
            }
            for r in bear_rebuttals
        ]
        
        bull_rebuttals_dict = [
            {
                "target_claim": r.target_claim,
                "counter_argument": r.counter_argument,
                "counter_evidence": r.counter_evidence,
                "strength": r.strength
            }
            for r in bull_rebuttals
        ]
        
        logger.info(f"Bear rebuttals: {len(bear_rebuttals_dict)}, Bull rebuttals: {len(bull_rebuttals_dict)}")
        
        # Step 4: Phase 3 - Synthesis with Evidence Grading
        logger.info("Phase 3: Synthesis")
        
        verdict = await synthesizer.synthesize(
            ticker,
            bull_dict,
            bear_dict,
            bull_rebuttals_dict,
            bear_rebuttals_dict,
            fundamentals
        )
        
        logger.info(f"Verdict: {verdict.recommendation} (conviction: {verdict.conviction:.2f})")
        logger.info(f"Probabilities - Bull: {verdict.bull_probability:.2f}, Base: {verdict.base_probability:.2f}, Bear: {verdict.bear_probability:.2f}")
        
        # Return combined result
        return {
            "ticker": ticker,
            "analysis_type": "adversarial_debate",
            "verdict": verdict.to_dict(),
            "bull_case": bull_dict,
            "bear_case": bear_dict,
            "rebuttals": {
                "bear_to_bull": bear_rebuttals_dict,
                "bull_to_bear": bull_rebuttals_dict
            },
            "fundamentals": fundamentals,
            "headlines": headlines,
            "timestamp": datetime.now().isoformat(),
            "error": None
        }
        
    except Exception as e:
        logger.error(f"Debate analysis failed for {ticker}: {e}")
        return {
            "ticker": ticker,
            "analysis_type": "adversarial_debate",
            "verdict": None,
            "bull_case": None,
            "bear_case": None,
            "rebuttals": None,
            "fundamentals": None,
            "headlines": None,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


def run_debate_analysis_sync(ticker: str) -> Dict:
    """Synchronous wrapper for run_debate_analysis."""
    return asyncio.run(run_debate_analysis(ticker))