"""
Streaming Analysis Module for StockSense.

Stage 4: Streaming Analysis with Server-Sent Events (SSE)

This module provides:
1. An async generator for streaming analysis with progress events
2. SSE endpoint for progressive result rendering
"""

import asyncio
import json
import logging
from typing import Dict, Any, AsyncGenerator, Callable, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("stocksense.streaming")


class StreamEventType(str, Enum):
    """Types of streaming events."""
    STARTED = "started"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    PROGRESS = "progress"
    COMPLETED = "completed"
    ERROR = "error"
    # Phase 3: Debate-specific events
    DEBATE_STARTED = "debate_started"
    BULL_DRAFTING = "bull_drafting"
    BEAR_DRAFTING = "bear_drafting"
    BULL_COMPLETE = "bull_complete"
    BEAR_COMPLETE = "bear_complete"
    REBUTTAL_ROUND = "rebuttal_round"
    SYNTHESIS_STARTED = "synthesis_started"
    DEBATE_COMPLETED = "debate_completed"


@dataclass
class StreamEvent:
    """A streaming event sent to the client."""
    event_type: StreamEventType
    tool_name: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_sse(self) -> str:
        """Convert to SSE format."""
        event_data = {
            "type": self.event_type.value,
            "tool": self.tool_name,
            "progress": self.progress,
            "message": self.message,
            "timestamp": self.timestamp,
        }
        if self.data:
            event_data["data"] = self.data
        
        return f"data: {json.dumps(event_data)}\n\n"


# Tool sequence for progress calculation
TOOL_SEQUENCE = [
    "fetch_news_headlines",
    "fetch_price_data", 
    "analyze_sentiment",
    "generate_skeptic_critique"
]


def calculate_progress(tools_completed: list) -> float:
    """Calculate progress based on completed tools."""
    completed_count = sum(1 for tool in TOOL_SEQUENCE if tool in tools_completed)
    return min(completed_count / len(TOOL_SEQUENCE), 1.0)


async def run_streaming_analysis(
    ticker: str,
    event_callback: Optional[Callable[[StreamEvent], None]] = None
) -> AsyncGenerator[StreamEvent, None]:
    """
    Run ReAct analysis with streaming events.
    
    Yields StreamEvent objects as the analysis progresses.
    Optionally calls event_callback for each event.
    
    Args:
        ticker: Stock ticker symbol
        event_callback: Optional callback for each event
    
    Yields:
        StreamEvent objects for each stage of analysis
    """
    from .react_flow import tools, AgentState
    from langchain_core.messages import HumanMessage, ToolMessage
    from stocksense.core.config import get_chat_llm
    
    ticker = ticker.upper().strip()
    tools_used = []
    
    def emit(event: StreamEvent):
        if event_callback:
            event_callback(event)
        return event
    
    # Emit start event
    yield emit(StreamEvent(
        event_type=StreamEventType.STARTED,
        message=f"Starting analysis for {ticker}",
        progress=0.0
    ))
    
    # Initialize state
    state: AgentState = {
        "messages": [],
        "ticker": ticker,
        "headlines": [],
        "price_data": [],
        "sentiment_report": "",
        "summary": "",
        "reasoning_steps": [],
        "tools_used": [],
        "iterations": 0,
        "max_iterations": 10,
        "final_decision": "",
        "error": None,
        "overall_sentiment": "",
        "overall_confidence": 0.0,
        "confidence_reasoning": "",
        "headline_analyses": [],
        "key_themes": [],
        "potential_impact": "",
        "risks_identified": [],
        "information_gaps": [],
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
        # Import tools
        from .react_flow import (
            fetch_news_headlines,
            fetch_price_data,
            analyze_sentiment,
            generate_skeptic_critique
        )
        
        # Step 1: Fetch news headlines
        yield emit(StreamEvent(
            event_type=StreamEventType.TOOL_STARTED,
            tool_name="fetch_news_headlines",
            message="Fetching news headlines...",
            progress=0.05
        ))
        
        news_result = fetch_news_headlines.invoke({"ticker": ticker, "days": 7})
        tools_used.append("fetch_news_headlines")
        
        if news_result.get("success"):
            state["headlines"] = news_result.get("headlines", [])
        
        yield emit(StreamEvent(
            event_type=StreamEventType.TOOL_COMPLETED,
            tool_name="fetch_news_headlines",
            message=f"Found {len(state['headlines'])} headlines",
            progress=0.25,
            data={"headlines_count": len(state["headlines"]), "headlines": state["headlines"][:5]}
        ))
        
        # Small delay for effect
        await asyncio.sleep(0.1)
        
        # Step 2: Fetch price data
        yield emit(StreamEvent(
            event_type=StreamEventType.TOOL_STARTED,
            tool_name="fetch_price_data",
            message="Fetching price history...",
            progress=0.30
        ))
        
        price_result = fetch_price_data.invoke({"ticker": ticker, "period": "1mo"})
        tools_used.append("fetch_price_data")
        
        if price_result.get("success"):
            state["price_data"] = price_result.get("price_data", [])
        
        yield emit(StreamEvent(
            event_type=StreamEventType.TOOL_COMPLETED,
            tool_name="fetch_price_data",
            message=f"Retrieved {len(state['price_data'])} data points",
            progress=0.45,
            data={"data_points": len(state["price_data"]), "price_data": state["price_data"]}
        ))
        
        await asyncio.sleep(0.1)
        
        # Step 3: Analyze sentiment
        if state["headlines"]:
            yield emit(StreamEvent(
                event_type=StreamEventType.TOOL_STARTED,
                tool_name="analyze_sentiment",
                message="Analyzing sentiment...",
                progress=0.50
            ))
            
            sentiment_result = analyze_sentiment.invoke({"headlines": state["headlines"]})
            tools_used.append("analyze_sentiment")
            
            if sentiment_result.get("success"):
                state["sentiment_report"] = sentiment_result.get("sentiment_report", "")
                state["overall_sentiment"] = sentiment_result.get("overall_sentiment", "")
                state["overall_confidence"] = sentiment_result.get("overall_confidence", 0.0)
                state["confidence_reasoning"] = sentiment_result.get("confidence_reasoning", "")
                state["headline_analyses"] = sentiment_result.get("headline_analyses", [])
                state["key_themes"] = sentiment_result.get("key_themes", [])
                state["potential_impact"] = sentiment_result.get("potential_impact", "")
                state["risks_identified"] = sentiment_result.get("risks_identified", [])
                state["information_gaps"] = sentiment_result.get("information_gaps", [])
            
            yield emit(StreamEvent(
                event_type=StreamEventType.TOOL_COMPLETED,
                tool_name="analyze_sentiment",
                message=f"Sentiment: {state['overall_sentiment']} ({state['overall_confidence']:.0%} confidence)",
                progress=0.70,
                data={
                    "overall_sentiment": state["overall_sentiment"],
                    "overall_confidence": state["overall_confidence"],
                    "key_themes": state["key_themes"][:3],
                    "risks_identified": state["risks_identified"][:3]
                }
            ))
            
            await asyncio.sleep(0.1)
            
            # Step 4: Generate skeptic critique
            yield emit(StreamEvent(
                event_type=StreamEventType.TOOL_STARTED,
                tool_name="generate_skeptic_critique",
                message="Generating skeptic analysis...",
                progress=0.75
            ))
            
            skeptic_result = generate_skeptic_critique.invoke({
                "ticker": ticker,
                "headlines": state["headlines"],
                "primary_sentiment": state["overall_sentiment"],
                "primary_confidence": state["overall_confidence"]
            })
            tools_used.append("generate_skeptic_critique")
            
            if skeptic_result.get("success"):
                state["skeptic_report"] = skeptic_result.get("skeptic_report", "")
                state["skeptic_sentiment"] = skeptic_result.get("skeptic_sentiment", "")
                state["skeptic_confidence"] = skeptic_result.get("skeptic_confidence", 0.0)
                state["primary_disagreement"] = skeptic_result.get("primary_disagreement", "")
                state["critiques"] = skeptic_result.get("critiques", [])
                state["bear_cases"] = skeptic_result.get("bear_cases", [])
                state["hidden_risks"] = skeptic_result.get("hidden_risks", [])
                state["would_change_mind"] = skeptic_result.get("would_change_mind", [])
            
            yield emit(StreamEvent(
                event_type=StreamEventType.TOOL_COMPLETED,
                tool_name="generate_skeptic_critique",
                message=f"Skeptic verdict: {state['skeptic_sentiment']}",
                progress=0.90,
                data={
                    "skeptic_sentiment": state["skeptic_sentiment"],
                    "skeptic_confidence": state["skeptic_confidence"],
                    "primary_disagreement": state["primary_disagreement"],
                    "bear_cases": state["bear_cases"][:2]
                }
            ))
        
        # Generate summary
        summary = f"""
Stock Analysis Summary for {ticker}:

Market Sentiment: {state['overall_sentiment']} (Confidence: {state['overall_confidence']:.0%})
{state['confidence_reasoning']}

Key Findings:
- News Coverage: {len(state['headlines'])} articles analyzed
- Price Data: {len(state['price_data'])} data points
- Skeptic View: {state['skeptic_sentiment']}

Analysis completed using streaming mode.
        """.strip()
        
        state["summary"] = summary
        state["tools_used"] = tools_used
        state["iterations"] = 1
        
        # Final completed event with full data
        final_data = {
            "ticker": ticker,
            "summary": summary,
            "sentiment_report": state["sentiment_report"],
            "headlines": state["headlines"],
            "price_data": state["price_data"],
            "overall_sentiment": state["overall_sentiment"],
            "overall_confidence": state["overall_confidence"],
            "confidence_reasoning": state["confidence_reasoning"],
            "key_themes": state["key_themes"],
            "risks_identified": state["risks_identified"],
            "information_gaps": state["information_gaps"],
            "skeptic_report": state["skeptic_report"],
            "skeptic_sentiment": state["skeptic_sentiment"],
            "skeptic_confidence": state["skeptic_confidence"],
            "primary_disagreement": state["primary_disagreement"],
            "critiques": state["critiques"],
            "bear_cases": state["bear_cases"],
            "hidden_risks": state["hidden_risks"],
            "would_change_mind": state["would_change_mind"],
            "tools_used": tools_used,
            "timestamp": datetime.now().isoformat()
        }
        
        yield emit(StreamEvent(
            event_type=StreamEventType.COMPLETED,
            message=f"Analysis complete for {ticker}",
            progress=1.0,
            data=final_data
        ))
        
    except Exception as e:
        logger.error(f"Streaming analysis error: {e}")
        yield emit(StreamEvent(
            event_type=StreamEventType.ERROR,
            message=str(e),
            progress=calculate_progress(tools_used)
        ))


# ============================================================================
# Phase 3: Streaming Debate Analysis
# ============================================================================

async def run_streaming_debate_analysis(
    ticker: str,
    event_callback: Optional[Callable[[StreamEvent], None]] = None
) -> AsyncGenerator[StreamEvent, None]:
    """
    Run adversarial debate analysis with streaming events.
    
    Yields StreamEvent objects as the debate progresses through phases:
    1. Data Collection
    2. Bull Drafting (parallel with Bear)
    3. Bear Drafting (parallel with Bull)
    4. Rebuttal Round
    5. Synthesis
    
    Args:
        ticker: Stock ticker symbol
        event_callback: Optional callback for each event
    
    Yields:
        StreamEvent objects for each stage of the debate
    """
    from stocksense.core.data_collectors import get_news, get_price_history, get_fundamental_data
    from stocksense.core.analyzer import analyze_sentiment_structured
    from stocksense.agents import BullAnalyst, BearAnalyst, Synthesizer
    
    ticker = ticker.upper().strip()
    
    def emit(event: StreamEvent):
        if event_callback:
            event_callback(event)
        return event
    
    try:
        # Phase 0: Start
        yield emit(StreamEvent(
            event_type=StreamEventType.DEBATE_STARTED,
            message=f"Starting adversarial debate for {ticker}",
            progress=0.0
        ))
        
        # Phase 1: Data Collection
        yield emit(StreamEvent(
            event_type=StreamEventType.TOOL_STARTED,
            tool_name="collect_data",
            message="Collecting market data...",
            progress=0.05
        ))
        
        # Collect data in parallel
        fundamentals = await asyncio.to_thread(get_fundamental_data, ticker)
        headlines = await asyncio.to_thread(get_news, ticker, 7)
        price_data = await asyncio.to_thread(get_price_history, ticker, "1mo")
        
        if fundamentals is None:
            fundamentals = {}
        
        yield emit(StreamEvent(
            event_type=StreamEventType.TOOL_COMPLETED,
            tool_name="collect_data",
            message=f"Collected {len(headlines)} headlines",
            progress=0.15,
            data={"headlines_count": len(headlines)}
        ))
        
        # Sentiment analysis
        sentiment_analysis = {}
        if headlines:
            yield emit(StreamEvent(
                event_type=StreamEventType.TOOL_STARTED,
                tool_name="analyze_sentiment",
                message="Analyzing market sentiment...",
                progress=0.18
            ))
            
            try:
                sentiment_result = await asyncio.to_thread(
                    analyze_sentiment_structured, headlines
                )
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
            
            yield emit(StreamEvent(
                event_type=StreamEventType.TOOL_COMPLETED,
                tool_name="analyze_sentiment",
                message=f"Sentiment: {sentiment_analysis.get('overall_sentiment', 'Unknown')}",
                progress=0.25
            ))
        
        # Initialize agents
        bull_agent = BullAnalyst()
        bear_agent = BearAnalyst()
        synthesizer = Synthesizer()
        
        # Phase 2: Bull and Bear Drafting (parallel)
        yield emit(StreamEvent(
            event_type=StreamEventType.BULL_DRAFTING,
            message="Bull analyst building growth case...",
            progress=0.30
        ))
        
        yield emit(StreamEvent(
            event_type=StreamEventType.BEAR_DRAFTING,
            message="Bear analyst identifying risks...",
            progress=0.30
        ))
        
        # Run Bull and Bear in parallel
        bull_task = bull_agent.analyze(
            ticker, fundamentals, headlines, price_data, sentiment_analysis
        )
        bear_task = bear_agent.analyze(
            ticker, fundamentals, headlines, price_data, sentiment_analysis
        )
        
        bull_case, bear_case = await asyncio.gather(bull_task, bear_task)
        
        bull_dict = bull_case.to_dict()
        bear_dict = bear_case.to_dict()
        
        yield emit(StreamEvent(
            event_type=StreamEventType.BULL_COMPLETE,
            message=f"Bull case complete: {bull_case.confidence:.0%} confident",
            progress=0.50,
            data={
                "thesis": bull_dict.get("thesis", "")[:100],
                "confidence": bull_case.confidence,
                "catalysts_count": len(bull_dict.get("catalysts", []))
            }
        ))
        
        yield emit(StreamEvent(
            event_type=StreamEventType.BEAR_COMPLETE,
            message=f"Bear case complete: {bear_case.confidence:.0%} confident",
            progress=0.55,
            data={
                "thesis": bear_dict.get("thesis", "")[:100],
                "confidence": bear_case.confidence,
                "risks_count": len(bear_dict.get("risks", []))
            }
        ))
        
        # Phase 3: Rebuttal Round
        yield emit(StreamEvent(
            event_type=StreamEventType.REBUTTAL_ROUND,
            message="Agents cross-examining each other's arguments...",
            progress=0.60
        ))
        
        # Bear rebuts Bull
        bear_rebuttals = await bear_agent.generate_rebuttal(
            bull_dict, bear_dict, fundamentals
        )
        
        # Bull rebuts Bear
        bull_rebuttals = await bull_agent.generate_rebuttal(
            bear_dict, bull_dict, fundamentals
        )
        
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
        
        yield emit(StreamEvent(
            event_type=StreamEventType.PROGRESS,
            message=f"Rebuttal round complete: {len(bear_rebuttals)} vs {len(bull_rebuttals)} rebuttals",
            progress=0.75,
            data={
                "bear_rebuttals_count": len(bear_rebuttals_dict),
                "bull_rebuttals_count": len(bull_rebuttals_dict)
            }
        ))
        
        # Phase 4: Synthesis
        yield emit(StreamEvent(
            event_type=StreamEventType.SYNTHESIS_STARTED,
            message="Synthesizer weighing arguments and grading evidence...",
            progress=0.80
        ))
        
        verdict = await synthesizer.synthesize(
            ticker,
            bull_dict,
            bear_dict,
            bull_rebuttals_dict,
            bear_rebuttals_dict,
            fundamentals
        )
        
        # Final result
        final_data = {
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
        
        yield emit(StreamEvent(
            event_type=StreamEventType.DEBATE_COMPLETED,
            message=f"Debate complete: {verdict.recommendation} ({verdict.conviction:.0%} conviction)",
            progress=1.0,
            data=final_data
        ))
        
    except Exception as e:
        logger.error(f"Streaming debate error: {e}")
        yield emit(StreamEvent(
            event_type=StreamEventType.ERROR,
            message=str(e),
            progress=0.0
        ))
