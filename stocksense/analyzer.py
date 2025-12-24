"""
Sentiment analysis module using structured LLM outputs.

This module performs sentiment analysis on news headlines using Google Gemini,
with structured Pydantic outputs for reliable parsing and honest uncertainty.
"""

import os
import json
from typing import List
from datetime import datetime

from .config import get_chat_llm, ConfigurationError
from .schemas import (
    HeadlineSentiment,
    SentimentAnalysisResult,
    KeyTheme,
)


def analyze_sentiment_of_headlines(headlines: List[str]) -> str:
    """
    Legacy function: Analyze sentiment and return formatted string.
    
    This maintains backward compatibility while using the new structured analysis internally.
    """
    if not headlines:
        return "No headlines provided for analysis."
    
    try:
        result = analyze_sentiment_structured(headlines)
        return format_sentiment_result(result)
    except Exception as e:
        # Fallback to legacy behavior on error
        return f"Error during sentiment analysis: {str(e)}"


def analyze_sentiment_structured(headlines: List[str]) -> SentimentAnalysisResult:
    """
    Analyze sentiment with structured output.
    
    Returns a validated Pydantic model with per-headline analysis,
    confidence levels, and explicit uncertainty.
    """
    if not headlines:
        return SentimentAnalysisResult(
            overall_sentiment="Insufficient Data",
            overall_confidence=0.0,
            confidence_reasoning="No headlines were provided for analysis.",
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            insufficient_data_count=0,
            headline_analyses=[],
            key_themes=[],
            potential_impact="Uncertain",
            risks_identified=[],
            information_gaps=["No news data available for analysis"]
        )
    
    try:
        llm = get_chat_llm(
            model="gemini-2.5-flash-lite",
            temperature=0.2,  # Lower temperature for more consistent structured output
            max_output_tokens=4096
        )
        
        # Build the analysis prompt
        numbered_headlines = "\n".join([f"{i+1}. {h}" for i, h in enumerate(headlines)])
        
        prompt = f"""You are a financial sentiment analyst. Analyze the following news headlines and provide a structured assessment.

HEADLINES TO ANALYZE:
{numbered_headlines}

INSTRUCTIONS:
1. Analyze each headline individually for sentiment (Bullish, Bearish, Neutral, or "Insufficient Data" if ambiguous)
2. Provide a confidence score (0.0 to 1.0) for each classification - be honest about uncertainty
3. Identify 2-4 key themes across the headlines
4. Assess overall market sentiment and potential price impact
5. List any risks mentioned and information gaps

IMPORTANT GUIDELINES:
- Use "Insufficient Data" when a headline is too vague or lacks context
- Lower confidence scores for headlines with mixed signals
- Be explicit about what you don't know
- Do not assume positive sentiment just because a company is mentioned

Respond with a JSON object matching this exact structure:
{{
    "overall_sentiment": "Bullish" | "Bearish" | "Neutral" | "Insufficient Data",
    "overall_confidence": <float 0.0-1.0>,
    "confidence_reasoning": "<explain what affected confidence>",
    "bullish_count": <int>,
    "bearish_count": <int>,
    "neutral_count": <int>,
    "insufficient_data_count": <int>,
    "headline_analyses": [
        {{
            "headline": "<original headline>",
            "sentiment": "Bullish" | "Bearish" | "Neutral" | "Insufficient Data",
            "confidence": <float 0.0-1.0>,
            "reasoning": "<1-2 sentence explanation>",
            "key_entities": ["<entity1>", "<entity2>"]
        }}
    ],
    "key_themes": [
        {{
            "theme": "<theme name>",
            "sentiment_direction": "Bullish" | "Bearish" | "Mixed",
            "headline_count": <int>,
            "summary": "<brief explanation>"
        }}
    ],
    "potential_impact": "Strong Positive" | "Moderate Positive" | "Minimal" | "Moderate Negative" | "Strong Negative" | "Uncertain",
    "risks_identified": ["<risk1>", "<risk2>"],
    "information_gaps": ["<gap1>", "<gap2>"]
}}

Return ONLY the JSON object, no additional text."""
        
        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Parse the JSON response
        
        # Clean up response - handle markdown code blocks
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        data = json.loads(cleaned)
        
        # Build the structured result
        headline_analyses = [
            HeadlineSentiment(**ha) for ha in data.get("headline_analyses", [])
        ]
        
        key_themes = [
            KeyTheme(**kt) for kt in data.get("key_themes", [])
        ]
        
        return SentimentAnalysisResult(
            overall_sentiment=data.get("overall_sentiment", "Neutral"),
            overall_confidence=data.get("overall_confidence", 0.5),
            confidence_reasoning=data.get("confidence_reasoning", ""),
            bullish_count=data.get("bullish_count", 0),
            bearish_count=data.get("bearish_count", 0),
            neutral_count=data.get("neutral_count", 0),
            insufficient_data_count=data.get("insufficient_data_count", 0),
            headline_analyses=headline_analyses,
            key_themes=key_themes,
            potential_impact=data.get("potential_impact", "Uncertain"),
            risks_identified=data.get("risks_identified", []),
            information_gaps=data.get("information_gaps", [])
        )
        
    except json.JSONDecodeError as e:
        # Return a valid result indicating parsing failure
        return SentimentAnalysisResult(
            overall_sentiment="Insufficient Data",
            overall_confidence=0.0,
            confidence_reasoning=f"Failed to parse LLM response as structured JSON: {str(e)}",
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            insufficient_data_count=len(headlines),
            headline_analyses=[],
            key_themes=[],
            potential_impact="Uncertain",
            risks_identified=[],
            information_gaps=["Analysis could not be completed due to response parsing error"]
        )
    except ConfigurationError as e:
        return SentimentAnalysisResult(
            overall_sentiment="Insufficient Data",
            overall_confidence=0.0,
            confidence_reasoning=f"Configuration error: {str(e)}",
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            insufficient_data_count=len(headlines),
            headline_analyses=[],
            key_themes=[],
            potential_impact="Uncertain",
            risks_identified=[],
            information_gaps=["Analysis could not be completed due to configuration error"]
        )
    except Exception as e:
        return SentimentAnalysisResult(
            overall_sentiment="Insufficient Data",
            overall_confidence=0.0,
            confidence_reasoning=f"Analysis error: {str(e)}",
            bullish_count=0,
            bearish_count=0,
            neutral_count=0,
            insufficient_data_count=len(headlines),
            headline_analyses=[],
            key_themes=[],
            potential_impact="Uncertain",
            risks_identified=[],
            information_gaps=["Analysis could not be completed due to unexpected error"]
        )


def format_sentiment_result(result: SentimentAnalysisResult) -> str:
    """
    Format structured sentiment result as a readable string.
    
    This provides backward compatibility with code expecting string output.
    """
    lines = []
    
    # Overall sentiment header
    lines.append(f"## Overall Sentiment: {result.overall_sentiment}")
    lines.append(f"**Confidence:** {result.overall_confidence:.0%}")
    lines.append(f"**Reasoning:** {result.confidence_reasoning}")
    lines.append("")
    
    # Breakdown
    lines.append("### Sentiment Breakdown")
    lines.append(f"- Bullish: {result.bullish_count}")
    lines.append(f"- Bearish: {result.bearish_count}")
    lines.append(f"- Neutral: {result.neutral_count}")
    if result.insufficient_data_count > 0:
        lines.append(f"- Insufficient Data: {result.insufficient_data_count}")
    lines.append("")
    
    # Key themes
    if result.key_themes:
        lines.append("### Key Themes")
        for theme in result.key_themes:
            lines.append(f"- **{theme.theme}** ({theme.sentiment_direction}): {theme.summary}")
        lines.append("")
    
    # Market impact
    lines.append(f"### Potential Market Impact: {result.potential_impact}")
    lines.append("")
    
    # Risks
    if result.risks_identified:
        lines.append("### Risks Identified")
        for risk in result.risks_identified:
            lines.append(f"- {risk}")
        lines.append("")
    
    # Information gaps (epistemic honesty)
    if result.information_gaps:
        lines.append("### What We Don't Know")
        for gap in result.information_gaps:
            lines.append(f"- {gap}")
        lines.append("")
    
    # Per-headline analysis
    if result.headline_analyses:
        lines.append("### Per-Headline Analysis")
        for i, ha in enumerate(result.headline_analyses, 1):
            sentiment_emoji = {"Bullish": "📈", "Bearish": "📉", "Neutral": "➡️", "Insufficient Data": "❓"}.get(ha.sentiment, "")
            lines.append(f"{i}. {sentiment_emoji} **{ha.sentiment}** ({ha.confidence:.0%}): {ha.headline[:80]}...")
            lines.append(f"   _{ha.reasoning}_")
        lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    sample_headlines = [
        "Apple Reports Record Q4 Earnings, Beats Wall Street Expectations",
        "Apple Stock Falls 3% After iPhone Sales Disappoint Analysts",
        "Apple Announces New AI Features for iPhone and iPad",
        "Regulatory Concerns Mount Over Apple's App Store Policies"
    ]
    
    # Test structured analysis
    result = analyze_sentiment_structured(sample_headlines)
    print("=== Structured Result ===")
    print(f"Overall: {result.overall_sentiment} ({result.overall_confidence:.0%})")
    print(f"Themes: {[t.theme for t in result.key_themes]}")
    print(f"Risks: {result.risks_identified}")
    print(f"Gaps: {result.information_gaps}")
    print("\n=== Formatted Output ===")
    print(format_sentiment_result(result))