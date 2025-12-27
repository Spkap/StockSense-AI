"""
Bull Analyst Agent

Growth-focused analyst that identifies investment opportunities,
competitive moats, and upside potential.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .base_agent import BaseAnalystAgent, AgentToolConfig, Claim, Rebuttal

logger = logging.getLogger("stocksense.agents.bull")


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
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # Parse JSON response
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            analysis = json.loads(content)
            
            return BullCase(
                ticker=ticker,
                thesis=analysis.get("thesis", ""),
                catalysts=[
                    Catalyst(
                        description=c.get("description", ""),
                        timeframe=c.get("timeframe", "medium-term"),
                        probability=float(c.get("probability", 0.5)),
                        potential_impact=c.get("potential_impact", "medium")
                    )
                    for c in analysis.get("catalysts", [])
                ],
                key_metrics=analysis.get("key_metrics", {}),
                upside_reasoning=analysis.get("upside_reasoning", ""),
                confidence=float(analysis.get("confidence", 0.5)),
                weaknesses=analysis.get("weaknesses", []),
                key_claims=[
                    Claim(
                        statement=c.get("statement", ""),
                        evidence=c.get("evidence", ""),
                        confidence=float(c.get("confidence", 0.5)),
                        data_source=c.get("data_source", "fundamentals")
                    )
                    for c in analysis.get("key_claims", [])
                ]
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
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            rebuttals_data = json.loads(content)
            
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
        info = fundamentals.get("info", {})
        
        # Format key metrics
        metrics_str = "\n".join([
            f"- {k}: {v}" for k, v in list(info.items())[:15]
        ])
        
        # Format headlines
        headlines_str = "\n".join([f"- {h}" for h in headlines[:10]])
        
        # Format sentiment themes
        themes = sentiment.get("key_themes", [])
        themes_str = "\n".join([
            f"- {t.get('theme', '')}: {t.get('sentiment_direction', '')}"
            for t in themes[:5]
        ])
        
        return f"""{self._build_system_prompt()}

TICKER: {ticker}

KEY FINANCIAL METRICS (Growth-Weighted):
{metrics_str}

RECENT HEADLINES:
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
      "data_source": "fundamentals|news|price"
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
