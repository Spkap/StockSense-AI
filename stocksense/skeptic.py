"""
Skeptic analysis module for Stage 2: Visible Skepticism.

This module provides a contrarian perspective that critiques the primary analysis,
surfaces bear cases, and identifies assumptions that may be wrong.
"""

import json
from typing import List, Optional
from pydantic import BaseModel, Field

from .config import get_chat_llm, ConfigurationError
from .schemas import SentimentAnalysisResult


class SkepticCritique(BaseModel):
    """A specific critique of the primary analysis."""
    
    critique: str = Field(description="The specific point of disagreement or concern")
    assumption_challenged: str = Field(description="What assumption in the primary analysis this challenges")
    evidence: str = Field(description="Evidence or reasoning supporting this critique")


class BearCase(BaseModel):
    """A bear case argument against the bullish thesis."""
    
    argument: str = Field(description="The core bear case argument")
    trigger: str = Field(description="What event or data would validate this bear case")
    severity: str = Field(description="How severe this risk is: 'High', 'Medium', 'Low'")


class SkepticAnalysis(BaseModel):
    """Complete skeptic analysis output."""
    
    # Skeptic's overall take
    skeptic_sentiment: str = Field(
        description="Skeptic's view: 'Disagree', 'Partially Disagree', 'Agree with Reservations', 'Agree'"
    )
    
    # Main disagreement
    primary_disagreement: str = Field(
        description="The main point where the skeptic disagrees with or questions the primary analysis"
    )
    
    # Specific critiques
    critiques: List[SkepticCritique] = Field(
        default_factory=list,
        description="Specific critiques of the primary analysis (2-4)"
    )
    
    # Bear cases
    bear_cases: List[BearCase] = Field(
        default_factory=list,
        description="Bear case scenarios to consider (2-3)"
    )
    
    # What would change the skeptic's mind
    would_change_mind: List[str] = Field(
        default_factory=list,
        description="Evidence or events that would make the skeptic more bullish"
    )
    
    # Hidden risks
    hidden_risks: List[str] = Field(
        default_factory=list,
        description="Risks not adequately surfaced in the primary analysis"
    )
    
    # Confidence in skepticism
    skeptic_confidence: float = Field(
        ge=0.0, le=1.0,
        description="How confident the skeptic is in their critique (0.0 = weak critique, 1.0 = very strong)"
    )


def generate_skeptic_analysis(
    primary_analysis: SentimentAnalysisResult,
    headlines: List[str],
    ticker: str
) -> SkepticAnalysis:
    """
    Generate a skeptical critique of the primary sentiment analysis.
    
    The Skeptic Agent's job is to:
    1. Challenge the primary analysis's conclusions
    2. Surface hidden risks and assumptions
    3. Present bear cases even for bullish analysis
    4. Maintain epistemic honesty
    """
    
    if not headlines:
        return SkepticAnalysis(
            skeptic_sentiment="Agree with Reservations",
            primary_disagreement="Cannot provide critique without headlines to analyze",
            critiques=[],
            bear_cases=[],
            would_change_mind=["Actual headlines to analyze"],
            hidden_risks=["No data available for skeptical analysis"],
            skeptic_confidence=0.0
        )
    
    try:
        llm = get_chat_llm(
            model="gemini-2.5-flash-lite",
            temperature=0.3,  # Slightly higher for more varied critique
            max_output_tokens=2048
        )
        
        # Format primary analysis for context
        headlines_text = "\n".join([f"- {h}" for h in headlines])
        
        prompt = f"""You are a SKEPTIC ANALYST. Your job is to challenge and critique the following primary analysis.

TICKER: {ticker}

HEADLINES ANALYZED:
{headlines_text}

PRIMARY ANALYSIS CONCLUSION:
- Overall Sentiment: {primary_analysis.overall_sentiment}
- Confidence: {primary_analysis.overall_confidence:.0%}
- Potential Impact: {primary_analysis.potential_impact}
- Key Themes: {', '.join([t.theme for t in primary_analysis.key_themes]) if primary_analysis.key_themes else 'None identified'}
- Risks Identified: {', '.join(primary_analysis.risks_identified) if primary_analysis.risks_identified else 'None identified'}

YOUR MANDATE:
1. CHALLENGE the conclusions - find weaknesses in the reasoning
2. SURFACE bear cases - even if the analysis is bullish, find the bear case
3. IDENTIFY hidden risks - what dangers are not being adequately considered?
4. QUESTION assumptions - what must be true for this analysis to be correct?
5. BE SPECIFIC - don't just say "could be wrong", explain WHY and HOW

IMPORTANT: A good skeptic doesn't just disagree for the sake of it. Your critique should be substantive and evidence-based. If the primary analysis is genuinely strong, acknowledge that while still surfacing concerns.

Respond with a JSON object:
{{
    "skeptic_sentiment": "Disagree" | "Partially Disagree" | "Agree with Reservations" | "Agree",
    "primary_disagreement": "<your main point of contention with the analysis>",
    "critiques": [
        {{
            "critique": "<specific critique>",
            "assumption_challenged": "<what assumption this challenges>",
            "evidence": "<evidence or reasoning>"
        }}
    ],
    "bear_cases": [
        {{
            "argument": "<bear case argument>",
            "trigger": "<what would validate this>",
            "severity": "High" | "Medium" | "Low"
        }}
    ],
    "would_change_mind": ["<evidence that would make you more bullish>"],
    "hidden_risks": ["<risks not adequately surfaced>"],
    "skeptic_confidence": <float 0.0-1.0>
}}

Return ONLY the JSON object."""

        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up response
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        data = json.loads(cleaned)
        
        # Build structured result
        critiques = [
            SkepticCritique(**c) for c in data.get("critiques", [])
        ]
        
        bear_cases = [
            BearCase(**b) for b in data.get("bear_cases", [])
        ]
        
        return SkepticAnalysis(
            skeptic_sentiment=data.get("skeptic_sentiment", "Agree with Reservations"),
            primary_disagreement=data.get("primary_disagreement", ""),
            critiques=critiques,
            bear_cases=bear_cases,
            would_change_mind=data.get("would_change_mind", []),
            hidden_risks=data.get("hidden_risks", []),
            skeptic_confidence=data.get("skeptic_confidence", 0.5)
        )
        
    except json.JSONDecodeError as e:
        return SkepticAnalysis(
            skeptic_sentiment="Agree with Reservations",
            primary_disagreement=f"Could not generate structured critique: {str(e)}",
            critiques=[],
            bear_cases=[],
            would_change_mind=[],
            hidden_risks=["Skeptic analysis failed - treat primary analysis with extra caution"],
            skeptic_confidence=0.0
        )
    except Exception as e:
        return SkepticAnalysis(
            skeptic_sentiment="Agree with Reservations",
            primary_disagreement=f"Error generating critique: {str(e)}",
            critiques=[],
            bear_cases=[],
            would_change_mind=[],
            hidden_risks=["Skeptic analysis error - consider seeking alternative viewpoints"],
            skeptic_confidence=0.0
        )


def format_skeptic_analysis(analysis: SkepticAnalysis) -> str:
    """Format skeptic analysis as readable markdown."""
    lines = []
    
    lines.append("## 🔍 Skeptic's Perspective")
    lines.append(f"**Verdict:** {analysis.skeptic_sentiment} ({analysis.skeptic_confidence:.0%} confidence)")
    lines.append("")
    
    lines.append(f"**Primary Disagreement:** {analysis.primary_disagreement}")
    lines.append("")
    
    if analysis.critiques:
        lines.append("### Critiques")
        for c in analysis.critiques:
            lines.append(f"- **{c.critique}**")
            lines.append(f"  - Challenges: {c.assumption_challenged}")
            lines.append(f"  - Evidence: {c.evidence}")
        lines.append("")
    
    if analysis.bear_cases:
        lines.append("### Bear Cases to Consider")
        for b in analysis.bear_cases:
            severity_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(b.severity, "⚪")
            lines.append(f"- {severity_emoji} **{b.argument}**")
            lines.append(f"  - Trigger: {b.trigger}")
        lines.append("")
    
    if analysis.hidden_risks:
        lines.append("### Hidden Risks")
        for r in analysis.hidden_risks:
            lines.append(f"- ⚠️ {r}")
        lines.append("")
    
    if analysis.would_change_mind:
        lines.append("### What Would Change Our Mind")
        for w in analysis.would_change_mind:
            lines.append(f"- ✅ {w}")
    
    return "\n".join(lines)


if __name__ == '__main__':
    # Test with mock primary analysis
    from .schemas import SentimentAnalysisResult, KeyTheme
    
    mock_primary = SentimentAnalysisResult(
        overall_sentiment="Bullish",
        overall_confidence=0.75,
        confidence_reasoning="Strong earnings beat",
        bullish_count=2,
        bearish_count=1,
        neutral_count=0,
        insufficient_data_count=0,
        headline_analyses=[],
        key_themes=[KeyTheme(theme="Earnings", sentiment_direction="Bullish", headline_count=2, summary="Strong")],
        potential_impact="Moderate Positive",
        risks_identified=["Competition"],
        information_gaps=["Guidance details"]
    )
    
    headlines = [
        "Apple Reports Record Q4 Earnings",
        "iPhone Sales Beat Expectations",
        "Services Revenue Grows 20%"
    ]
    
    result = generate_skeptic_analysis(mock_primary, headlines, "AAPL")
    print(format_skeptic_analysis(result))
