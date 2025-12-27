"""
Bear Analyst Agent

Risk-focused analyst that identifies threats, red flags,
and downside risks.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

from .base_agent import BaseAnalystAgent, AgentToolConfig, Claim, Rebuttal

logger = logging.getLogger("stocksense.agents.bear")


@dataclass
class Risk:
    """A specific risk factor identified by the Bear analyst."""
    description: str
    category: str  # "financial", "competitive", "operational", "regulatory", "management"
    severity: str  # "low", "medium", "high", "critical"
    probability: float  # 0.0-1.0 likelihood of materialization
    timeframe: str  # "near-term", "medium-term", "long-term"


@dataclass
class BearCase:
    """The complete bear case for a stock."""
    ticker: str
    thesis: str  # Core risk thesis (2-3 sentences)
    risks: List[Risk]
    red_flags: List[str]  # Warning signs from data
    key_metrics: Dict[str, Any]  # Risk-focused quantitative data
    downside_reasoning: str  # Why the stock could decline
    confidence: float  # 0.0-1.0
    what_would_make_bullish: List[str]  # Conditions to change view
    key_claims: List[Claim]  # Specific claims with evidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ticker": self.ticker,
            "thesis": self.thesis,
            "risks": [
                {
                    "description": r.description,
                    "category": r.category,
                    "severity": r.severity,
                    "probability": r.probability,
                    "timeframe": r.timeframe
                }
                for r in self.risks
            ],
            "red_flags": self.red_flags,
            "key_metrics": self.key_metrics,
            "downside_reasoning": self.downside_reasoning,
            "confidence": self.confidence,
            "what_would_make_bullish": self.what_would_make_bullish,
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


class BearAnalyst(BaseAnalystAgent):
    """
    Risk-focused analyst agent.
    
    Mines data for risk signals, red flags, and downside catalysts.
    Receives fundamentals with debt_to_equity, profit_margins, pe_ratio first.
    """
    
    def __init__(self):
        super().__init__(AgentToolConfig.BEAR_CONFIG)
    
    async def analyze(
        self,
        ticker: str,
        fundamentals: Dict[str, Any],
        headlines: List[str],
        price_data: List[Dict[str, Any]],
        sentiment_analysis: Dict[str, Any]
    ) -> BearCase:
        """
        Construct the strongest possible bear case for caution.
        """
        if not self.llm:
            return self._fallback_analysis(ticker, fundamentals)
        
        # Prepare data with risk-weighted emphasis
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
            
            return BearCase(
                ticker=ticker,
                thesis=analysis.get("thesis", ""),
                risks=[
                    Risk(
                        description=r.get("description", ""),
                        category=r.get("category", "operational"),
                        severity=r.get("severity", "medium"),
                        probability=float(r.get("probability", 0.5)),
                        timeframe=r.get("timeframe", "medium-term")
                    )
                    for r in analysis.get("risks", [])
                ],
                red_flags=analysis.get("red_flags", []),
                key_metrics=analysis.get("key_metrics", {}),
                downside_reasoning=analysis.get("downside_reasoning", ""),
                confidence=float(analysis.get("confidence", 0.5)),
                what_would_make_bullish=analysis.get("what_would_make_bullish", []),
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
            logger.error(f"Bear analysis failed: {e}")
            return self._fallback_analysis(ticker, fundamentals)
    
    async def generate_rebuttal(
        self,
        opponent_case: Dict[str, Any],
        own_case: Dict[str, Any],
        fundamentals: Dict[str, Any]
    ) -> List[Rebuttal]:
        """
        Find factual flaws in the Bull case.
        
        This is the Anti-Sycophancy mechanism.
        """
        if not self.llm:
            return []
        
        prompt = f"""You are the Bear Analyst reviewing the Bull Analyst's case.

BULL CASE TO REBUT:
{json.dumps(opponent_case, indent=2)}

YOUR BEAR CASE:
{json.dumps(own_case, indent=2)}

AVAILABLE DATA:
{json.dumps(fundamentals.get("info", {}), indent=2)}

Your task: Find FACTUAL FLAWS in the Bull case.
- Does the Bull cherry-pick data or ignore risks?
- Are the Bull's growth projections realistic?
- Does the Bull ignore competitive threats or valuation concerns?

Return a JSON array of rebuttals:
[
  {{
    "target_claim": "The specific Bull claim you're rebutting",
    "counter_argument": "Your counter-argument",
    "counter_evidence": "Specific data that supports your rebuttal",
    "strength": 0.0-1.0
  }}
]

Be HONEST. If the Bull's points are valid, acknowledge them with lower strength scores.
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
            logger.error(f"Bear rebuttal generation failed: {e}")
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
        
        # Format key metrics (risk-weighted)
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

KEY FINANCIAL METRICS (Risk-Weighted):
{metrics_str}

RECENT HEADLINES:
{headlines_str}

SENTIMENT THEMES:
{themes_str}

Construct the STRONGEST POSSIBLE BEAR CASE for {ticker}.

Return a JSON object with this structure:
{{
  "thesis": "2-3 sentence core risk thesis",
  "risks": [
    {{
      "description": "Specific risk factor",
      "category": "financial|competitive|operational|regulatory|management",
      "severity": "low|medium|high|critical",
      "probability": 0.0-1.0,
      "timeframe": "near-term|medium-term|long-term"
    }}
  ],
  "red_flags": ["Warning sign 1", "..."],
  "key_metrics": {{"metric_name": "value with risk interpretation"}},
  "downside_reasoning": "Why this stock could decline significantly",
  "confidence": 0.0-1.0,
  "what_would_make_bullish": ["Condition 1 to change view", "..."],
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
    
    def _fallback_analysis(self, ticker: str, fundamentals: Dict[str, Any]) -> BearCase:
        """Fallback when LLM is unavailable."""
        info = fundamentals.get("info", {})
        
        return BearCase(
            ticker=ticker,
            thesis=f"Risk analysis of {ticker} based on available fundamental data.",
            risks=[],
            red_flags=[],
            key_metrics={
                "debt_to_equity": info.get("debt_to_equity"),
                "profit_margins": info.get("profit_margins"),
                "pe_ratio": info.get("pe_ratio")
            },
            downside_reasoning="LLM unavailable - manual review required.",
            confidence=0.3,
            what_would_make_bullish=["LLM analysis to validate bull case"],
            key_claims=[]
        )
