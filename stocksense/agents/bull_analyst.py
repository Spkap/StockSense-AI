"""
Bull Analyst Agent

Growth-focused analyst that identifies investment opportunities,
competitive moats, and upside potential.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from typing import Literal

from .base_agent import BaseAnalystAgent, AgentToolConfig, Claim, Rebuttal

logger = logging.getLogger("stocksense.agents.bull")


# ── Pydantic models for with_structured_output ──────────────────────────────

class CatalystModel(BaseModel):
    description: str
    timeframe: Literal["near-term", "medium-term", "long-term"] = "medium-term"
    probability: float = Field(ge=0.0, le=1.0)
    potential_impact: Literal["low", "medium", "high"] = "medium"


class ClaimModel(BaseModel):
    statement: str
    evidence: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    data_source: str = "fundamentals"


class BullLLMOutput(BaseModel):
    """Schema enforced by Gemini via with_structured_output."""
    thesis: str
    catalysts: list[CatalystModel]
    key_metrics: dict[str, str]
    upside_reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    weaknesses: list[str]
    key_claims: list[ClaimModel]


@dataclass
class Catalyst:
    """A specific catalyst that could drive stock appreciation."""
    description: str
    timeframe: str  # "near-term", "medium-term", "long-term"
    probability: float  # 0.0-1.0
    potential_impact: str  # "low", "medium", "high"


@dataclass
class BullCase:
    """The complete bull case for a stock."""
    ticker: str
    thesis: str  # Core investment thesis (2-3 sentences)
    catalysts: List[Catalyst]
    key_metrics: Dict[str, Any]  # Supporting quantitative data
    upside_reasoning: str  # Why the stock could go up
    confidence: float  # 0.0-1.0
    weaknesses: List[str]  # Acknowledged weaknesses in bull case
    key_claims: List[Claim]  # Specific claims with evidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "thesis": self.thesis,
            "catalysts": [
                {
                    "description": c.description,
                    "timeframe": c.timeframe,
                    "probability": c.probability,
                    "potential_impact": c.potential_impact
                }
                for c in self.catalysts
            ],
            "key_metrics": self.key_metrics,
            "upside_reasoning": self.upside_reasoning,
            "confidence": self.confidence,
            "weaknesses": self.weaknesses,
            "key_claims": [
                {
                    "statement": c.statement,
                    "evidence": c.evidence,
                    "confidence": c.confidence,
                    "data_source": c.data_source
                }
                for c in self.key_claims
            ]
        }


class BullAnalyst(BaseAnalystAgent):
    """
    Growth-focused analyst agent.
    
    Mines data for growth signals, competitive advantages, and catalysts.
    Receives fundamentals with revenue_growth, market_cap, forward_pe first.
    """
    
    def __init__(self):
        super().__init__(AgentToolConfig.BULL_CONFIG)

    def _build_system_prompt(self) -> str:
        from stocksense.core.prompts import get_prompt
        return get_prompt("bull_system_v1")
    
    async def analyze(
        self,
        ticker: str,
        fundamentals: Dict[str, Any],
        headlines: List[str],
        price_data: List[Dict[str, Any]],
        sentiment_analysis: Dict[str, Any]
    ) -> BullCase:
        """
        Construct the strongest possible bull case for investment.
        """
        if not self.llm:
            return self._fallback_analysis(ticker, fundamentals)
        
        # Prepare data with growth-weighted emphasis
        prioritized_fundamentals = self.prepare_fundamentals(fundamentals)
        filtered_sentiment = self.filter_sentiment_themes(headlines, sentiment_analysis)
        
        # Build the analysis prompt
        prompt = self._build_analysis_prompt(
            ticker, 
            prioritized_fundamentals,
            headlines,
            price_data,
            filtered_sentiment
        )
        
        try:
            structured_llm = self.llm.with_structured_output(BullLLMOutput)
            analysis: BullLLMOutput = structured_llm.invoke(prompt)

            return BullCase(
                ticker=ticker,
                thesis=analysis.thesis,
                catalysts=[
                    Catalyst(
                        description=c.description,
                        timeframe=c.timeframe,
                        probability=c.probability,
                        potential_impact=c.potential_impact,
                    )
                    for c in analysis.catalysts
                ],
                key_metrics=analysis.key_metrics,
                upside_reasoning=analysis.upside_reasoning,
                confidence=analysis.confidence,
                weaknesses=analysis.weaknesses,
                key_claims=[
                    Claim(
                        statement=c.statement,
                        evidence=c.evidence,
                        confidence=c.confidence,
                        data_source=c.data_source,
                    )
                    for c in analysis.key_claims
                ],
            )

        except Exception as e:
            logger.error(f"Bull analysis failed: {e}")
            return self._fallback_analysis(ticker, fundamentals)
    
    async def generate_rebuttal(
        self,
        opponent_case: Dict[str, Any],
        own_case: Dict[str, Any],
        fundamentals: Dict[str, Any]
    ) -> List[Rebuttal]:
        """
        Find factual flaws in the Bear case.
        
        This is the Anti-Sycophancy mechanism.
        """
        if not self.llm:
            return []
        
        prompt = f"""You are the Bull Analyst reviewing the Bear Analyst's case.

BEAR CASE TO REBUT:
{json.dumps(opponent_case, indent=2)}

YOUR BULL CASE:
{json.dumps(own_case, indent=2)}

AVAILABLE DATA:
{json.dumps(fundamentals.get("info", {}), indent=2)}

Your task: Find FACTUAL FLAWS in the Bear case. 
- Does the Bear misinterpret data?
- Does the Bear ignore important growth signals?
- Are the Bear's concerns outdated or already addressed?

Return a JSON array of rebuttals:
[
  {{
    "target_claim": "The specific Bear claim you're rebutting",
    "counter_argument": "Your counter-argument",
    "counter_evidence": "Specific data that supports your rebuttal",
    "strength": 0.0-1.0
  }}
]

Be HONEST. If the Bear's points are valid, acknowledge them with lower strength scores.
Only return the JSON array."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            from stocksense.core.llm_parser import parse_llm_json, LLMParseError
            try:
                rebuttals_data = parse_llm_json(content)
            except LLMParseError as e:
                logger.error(f"Bull rebuttal JSON parse failed: {e}")
                return []
            
            return [
                Rebuttal(
                    target_claim=r.get("target_claim", ""),
                    counter_argument=r.get("counter_argument", ""),
                    counter_evidence=r.get("counter_evidence"),
                    strength=float(r.get("strength", 0.5))
                )
                for r in rebuttals_data
            ]
            
        except Exception as e:
            logger.error(f"Bull rebuttal generation failed: {e}")
            return []
    
    def _build_analysis_prompt(
        self,
        ticker: str,
        fundamentals: Dict[str, Any],
        headlines: List[str],
        price_data: List[Dict[str, Any]],
        sentiment: Dict[str, Any]
    ) -> str:
        from stocksense.core.technical_analysis import compute_technical_signals, format_technical_signals

        info = fundamentals.get("info", {})

        # Format key metrics (growth-weighted ordering already applied by prepare_fundamentals)
        metrics_str = "\n".join([
            f"- {k}: {v}" for k, v in list(info.items())[:15]
        ])

        # Bull-biased headline filter: use base method (beats, upgrades, launches first)
        ordered_headlines = self.filter_headlines_for_perspective(headlines)[:10]
        headlines_str = "\n".join([f"- {h}" for h in ordered_headlines])

        # Sentiment themes
        themes = sentiment.get("key_themes", [])
        themes_str = "\n".join([
            f"- {t.get('theme', '')}: {t.get('sentiment_direction', '')}"
            for t in themes[:5]
        ])

        # Technical signals (price data now actively used in prompt)
        tech_signals = compute_technical_signals(price_data)
        tech_str = format_technical_signals(tech_signals)

        return f"""{self._build_system_prompt()}

TICKER: {ticker}

KEY FINANCIAL METRICS (Growth-Weighted):
{metrics_str}

{tech_str}

RECENT HEADLINES (Bull-Signal Priority):
{headlines_str}

SENTIMENT THEMES:
{themes_str}

Construct the STRONGEST POSSIBLE BULL CASE for {ticker}.

Return a JSON object with this structure:
{{
  "thesis": "2-3 sentence core investment thesis",
  "catalysts": [
    {{
      "description": "Specific catalyst",
      "timeframe": "near-term|medium-term|long-term",
      "probability": 0.0-1.0,
      "potential_impact": "low|medium|high"
    }}
  ],
  "key_metrics": {{"metric_name": "value with interpretation"}},
  "upside_reasoning": "Why this stock could appreciate significantly",
  "confidence": 0.0-1.0,
  "weaknesses": ["Acknowledged weakness 1", "..."],
  "key_claims": [
    {{
      "statement": "Specific factual claim",
      "evidence": "Data supporting this claim",
      "confidence": 0.0-1.0,
      "data_source": "fundamentals|news|price|technical"
    }}
  ]
}}

Return ONLY the JSON object."""
    
    def _fallback_analysis(self, ticker: str, fundamentals: Dict[str, Any]) -> BullCase:
        """Fallback when LLM is unavailable."""
        info = fundamentals.get("info", {})
        
        return BullCase(
            ticker=ticker,
            thesis=f"Analysis of {ticker} based on available fundamental data.",
            catalysts=[],
            key_metrics={
                "revenue_growth": info.get("revenue_growth"),
                "market_cap": info.get("market_cap"),
                "forward_pe": info.get("forward_pe")
            },
            upside_reasoning="LLM unavailable - manual review required.",
            confidence=0.3,
            weaknesses=["Automated analysis without LLM reasoning"],
            key_claims=[]
        )
