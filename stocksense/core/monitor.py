"""
Kill Criteria Monitoring Engine.

Stage 4: Active monitoring of user-defined kill criteria against analysis results.

This module:
1. Extracts actionable signals from analysis results
2. Compares signals against user-defined kill criteria
3. Creates alerts when potential matches are detected
"""

import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from stocksense.core.config import get_chat_llm, ConfigurationError
from stocksense.db.supabase_client import get_supabase_client

logger = logging.getLogger("stocksense.kill_monitor")


@dataclass
class Signal:
    """An extracted signal from analysis text."""
    text: str
    category: str  # financial, operational, market, competitive, management
    sentiment: str  # positive, negative, neutral
    confidence: float


@dataclass
class KillCriteriaMatch:
    """A potential match between a signal and kill criteria."""
    criteria: str
    signal: str
    match_confidence: float
    explanation: str


def extract_signals_from_analysis(
    summary: str,
    sentiment_report: str,
    key_themes: List[Dict[str, Any]],
    risks_identified: List[str],
    bear_cases: List[Dict[str, Any]],
    hidden_risks: List[str]
) -> List[Signal]:
    """
    Extract actionable signals from analysis results using LLM.
    
    Signals are concrete claims or observations that could be compared
    against user-defined kill criteria.
    """
    try:
        llm = get_chat_llm()
    except ConfigurationError as e:
        logger.warning(f"LLM not available for signal extraction: {e}")
        return []
    
    # Compile analysis context
    context_parts = [f"Analysis Summary:\n{summary}"]
    
    if key_themes:
        themes_text = "\n".join([
            f"- {t.get('theme', '')}: {t.get('sentiment_direction', '')} ({t.get('summary', '')})"
            for t in key_themes[:5]
        ])
        context_parts.append(f"Key Themes:\n{themes_text}")
    
    if risks_identified:
        risks_text = "\n".join([f"- {r}" for r in risks_identified[:5]])
        context_parts.append(f"Identified Risks:\n{risks_text}")
    
    if bear_cases:
        bear_text = "\n".join([
            f"- {bc.get('argument', '')} (trigger: {bc.get('trigger', '')})"
            for bc in bear_cases[:3]
        ])
        context_parts.append(f"Bear Cases:\n{bear_text}")
    
    if hidden_risks:
        hidden_text = "\n".join([f"- {r}" for r in hidden_risks[:3]])
        context_parts.append(f"Hidden Risks:\n{hidden_text}")
    
    analysis_context = "\n\n".join(context_parts)
    
    prompt = f"""Extract concrete, actionable signals from this stock analysis.

A signal is a specific claim, observation, or data point that an investor might use to evaluate their investment thesis.

{analysis_context}

Return a JSON array of signals. Each signal should have:
- "text": The signal itself (a specific, concrete statement)
- "category": One of: financial, operational, market, competitive, management
- "sentiment": One of: positive, negative, neutral
- "confidence": 0.0-1.0 indicating how clearly this signal is expressed

Focus on:
1. Financial metrics or changes (revenue, margins, growth rates)
2. Competitive position changes
3. Management or leadership changes
4. Market condition shifts
5. Operational concerns or improvements

Return ONLY the JSON array, no other text. Extract 3-8 key signals.
"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Parse JSON response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        signals_data = json.loads(content)
        
        signals = []
        for s in signals_data:
            signals.append(Signal(
                text=s.get("text", ""),
                category=s.get("category", "market"),
                sentiment=s.get("sentiment", "neutral"),
                confidence=float(s.get("confidence", 0.5))
            ))
        
        logger.info(f"Extracted {len(signals)} signals from analysis")
        return signals
        
    except Exception as e:
        logger.error(f"Signal extraction failed: {e}")
        return []


def match_signals_to_criteria(
    signals: List[Signal],
    kill_criteria: List[str],
    ticker: str
) -> List[KillCriteriaMatch]:
    """
    Compare extracted signals against user-defined kill criteria.
    
    Uses LLM to perform semantic matching since criteria are free-form text.
    """
    if not signals or not kill_criteria:
        return []
    
    try:
        llm = get_chat_llm()
    except ConfigurationError as e:
        logger.warning(f"LLM not available for criteria matching: {e}")
        return []
    
    signals_text = "\n".join([
        f"{i+1}. [{s.category}/{s.sentiment}] {s.text}"
        for i, s in enumerate(signals)
    ])
    
    criteria_text = "\n".join([
        f"{i+1}. {c}"
        for i, c in enumerate(kill_criteria)
    ])
    
    prompt = f"""You are evaluating whether any signals from a stock analysis might trigger an investor's pre-defined kill criteria (exit conditions).

TICKER: {ticker}

SIGNALS FROM ANALYSIS:
{signals_text}

USER'S KILL CRITERIA:
{criteria_text}

For each kill criteria, determine if ANY signal suggests it might be triggered or at risk.

Important:
- Be conservative. Only flag matches where the signal reasonably suggests the criteria might be met.
- Partial or emerging matches count (e.g., "slowing growth" matches "revenue growth below 10%")
- Consider the semantic meaning, not just keyword matches.

Return a JSON array of matches. Each match should have:
- "criteria_index": 0-based index of the kill criteria
- "signal_index": 0-based index of the matching signal
- "confidence": 0.0-1.0 (how confident you are this is a real match)
- "explanation": Brief explanation of why this is a match

If no criteria are potentially triggered, return an empty array: []

Return ONLY the JSON array.
"""
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # Parse JSON response
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        matches_data = json.loads(content)
        
        matches = []
        for m in matches_data:
            criteria_idx = m.get("criteria_index", 0)
            signal_idx = m.get("signal_index", 0)
            
            if criteria_idx < len(kill_criteria) and signal_idx < len(signals):
                matches.append(KillCriteriaMatch(
                    criteria=kill_criteria[criteria_idx],
                    signal=signals[signal_idx].text,
                    match_confidence=float(m.get("confidence", 0.5)),
                    explanation=m.get("explanation", "")
                ))
        
        logger.info(f"Found {len(matches)} potential kill criteria matches")
        return matches
        
    except Exception as e:
        logger.error(f"Criteria matching failed: {e}")
        return []


def create_kill_alert(
    user_id: str,
    access_token: str,
    thesis_id: str,
    ticker: str,
    match: KillCriteriaMatch,
    analysis_sentiment: str,
    analysis_confidence: float,
    analysis_summary: str
) -> Optional[Dict[str, Any]]:
    """
    Create a kill alert in the database.
    """
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        # Truncate summary for storage
        summary_excerpt = analysis_summary[:500] if len(analysis_summary) > 500 else analysis_summary
        
        # Phase 2: Write to alert_history
        message = f"Kill Criteria Triggered: {match.criteria}"
        
        data_json = {
            "triggered_criteria": match.criteria,
            "triggering_signal": match.signal,
            "match_confidence": match.match_confidence,
            "analysis_sentiment": analysis_sentiment,
            "analysis_confidence": analysis_confidence,
            "analysis_summary": summary_excerpt,
            "status": "pending"
        }
        
        row_data = {
            "user_id": user_id,
            "thesis_id": thesis_id,
            "ticker": ticker.upper(),
            "alert_type": "kill_criteria",
            "message": message,
            "data": data_json,
            "is_read": False
        }
        
        response = client.table("alert_history").insert(row_data).execute()
        alert = response.data[0] if response.data else None
        
        if alert:
            logger.info(f"Created alert_history entry for thesis {thesis_id}")
        
        return alert
        
    except Exception as e:
        logger.error(f"Failed to create kill alert: {e}")
        return None


def get_pending_alerts(user_id: str, access_token: str, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get pending kill alerts for a user.
    """
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        query = client.table("alert_history").select("*").eq("user_id", user_id).eq("is_read", False)
        
        if ticker:
            query = query.eq("ticker", ticker.upper())
        
        response = query.order("created_at", desc=True).execute()
        return response.data or []
        
    except Exception as e:
        logger.error(f"Failed to fetch pending alerts: {e}")
        return []


def update_alert_status(
    user_id: str,
    access_token: str,
    alert_id: str,
    status: str,
    user_action: Optional[str] = None
) -> bool:
    """
    Update the status of a kill alert.
    
    Status can be: pending, dismissed, acknowledged, acted
    """
    try:
        client = get_supabase_client()
        client.postgrest.auth(access_token)
        
        update_data = {"status": status, "is_read": True}
        if user_action:
            update_data["user_action"] = user_action
        if status != "pending":
            from datetime import datetime
            update_data["resolved_at"] = datetime.utcnow().isoformat()
        
        client.table("alert_history").update(update_data).eq("id", alert_id).eq("user_id", user_id).execute()
        return True
        
    except Exception as e:
        logger.error(f"Failed to update alert status: {e}")
        return False


def check_kill_criteria_for_ticker(
    ticker: str,
    analysis_result: Dict[str, Any],
    user_id: str,
    access_token: str
) -> List[Dict[str, Any]]:
    """
    Main entry point: Check if an analysis triggers any kill criteria for a user's theses.
    
    Args:
        ticker: Stock ticker symbol
        analysis_result: Full analysis result from ReAct agent
        user_id: User's UUID
        access_token: User's JWT for Supabase
    
    Returns:
        List of created alerts
    """
    from stocksense.db.supabase_client import get_user_theses
    
    # Get user's theses for this ticker
    theses = get_user_theses(user_id, access_token, ticker)
    
    if not theses:
        logger.debug(f"No theses found for {ticker}, skipping kill criteria check")
        return []
    
    # Filter to active theses with kill criteria
    active_theses = [
        t for t in theses 
        if t.get("status") == "active" and t.get("kill_criteria")
    ]
    
    if not active_theses:
        logger.debug(f"No active theses with kill criteria for {ticker}")
        return []
    
    # Extract signals from analysis
    signals = extract_signals_from_analysis(
        summary=analysis_result.get("summary", ""),
        sentiment_report=analysis_result.get("sentiment_report", ""),
        key_themes=analysis_result.get("key_themes", []),
        risks_identified=analysis_result.get("risks_identified", []),
        bear_cases=analysis_result.get("bear_cases", []),
        hidden_risks=analysis_result.get("hidden_risks", [])
    )
    
    if not signals:
        logger.debug(f"No signals extracted from analysis for {ticker}")
        return []
    
    created_alerts = []
    
    for thesis in active_theses:
        thesis_id = thesis["id"]
        kill_criteria = thesis.get("kill_criteria", [])
        
        # Match signals to this thesis's kill criteria
        matches = match_signals_to_criteria(signals, kill_criteria, ticker)
        
        # Create alerts for high-confidence matches (>0.6)
        for match in matches:
            if match.match_confidence >= 0.6:
                alert = create_kill_alert(
                    user_id=user_id,
                    access_token=access_token,
                    thesis_id=thesis_id,
                    ticker=ticker,
                    match=match,
                    analysis_sentiment=analysis_result.get("overall_sentiment", ""),
                    analysis_confidence=analysis_result.get("overall_confidence", 0.0),
                    analysis_summary=analysis_result.get("summary", "")
                )
                if alert:
                    created_alerts.append(alert)
    
    return created_alerts
