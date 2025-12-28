"""
Base Agent Infrastructure with Information Asymmetry

This module provides the foundation for specialized analyst agents with
different tool configurations that shape what data they prioritize.

Key Design: Information Asymmetry
- Bull Analyst receives growth-weighted data emphasis
- Bear Analyst receives risk-weighted data emphasis
- Both see the SAME underlying data, but with different ordering and emphasis
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from stocksense.core.config import get_chat_llm, ConfigurationError
from stocksense.core.data_collectors import get_news, get_price_history, get_fundamental_data

logger = logging.getLogger("stocksense.agents.base")


@dataclass
class AgentToolConfig:
    """
    Defines which data fields an agent prioritizes and how data is filtered.
    
    This creates genuine "Information Asymmetry" - agents aren't just 
    roleplay-ing different perspectives, they're actively mining different
    aspects of the same data.
    """
    
    # Bull Analyst prioritizes growth signals
    BULL_CONFIG = {
        "name": "Bull Analyst",
        "persona": "growth_focused",
        "fundamental_priority": [
            "revenue_growth",
            "market_cap", 
            "forward_pe",
            "recommendation_mean",
            "target_high",
            "target_mean"
        ],
        "sentiment_focus": [
            "positive_themes",
            "analyst_upgrades", 
            "product_launches",
            "market_expansion",
            "competitive_wins"
        ],
        "data_ordering": "growth_first"
    }
    
    # Bear Analyst prioritizes risk signals
    BEAR_CONFIG = {
        "name": "Bear Analyst",
        "persona": "risk_focused",
        "fundamental_priority": [
            "debt_to_equity",
            "profit_margins",
            "pe_ratio",
            "price_to_book",
            "current_ratio",
            "quick_ratio"
        ],
        "sentiment_focus": [
            "negative_themes",
            "insider_selling",
            "competitive_threats",
            "regulatory_risks",
            "margin_compression"
        ],
        "data_ordering": "risk_first"
    }


@dataclass
class Claim:
    """A specific claim made by an analyst with supporting evidence."""
    statement: str
    evidence: str
    confidence: float  # 0.0-1.0
    data_source: str  # Which tool/data supported this claim


@dataclass 
class Rebuttal:
    """A rebuttal to an opponent's claim."""
    target_claim: str
    counter_argument: str
    counter_evidence: Optional[str]
    strength: float  # 0.0-1.0 how strong is this rebuttal


class BaseAnalystAgent(ABC):
    """
    Abstract base class for analyst agents.
    
    Each agent receives the same raw data but processes it through
    different analytical lenses based on their configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config["name"]
        self.persona = config["persona"]
        self.fundamental_priority = config["fundamental_priority"]
        self.sentiment_focus = config["sentiment_focus"]
        
        try:
            self.llm = get_chat_llm(temperature=0.2)
        except ConfigurationError as e:
            logger.warning(f"LLM not available for {self.name}: {e}")
            self.llm = None
    
    def prepare_fundamentals(self, raw_fundamentals: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reorder fundamentals data to emphasize priority metrics.
        
        This is where Information Asymmetry happens - same data,
        different presentation order affects LLM attention.
        """
        if not raw_fundamentals:
            return {}
        
        info = raw_fundamentals.get("info", {})
        
        # Extract priority metrics first
        prioritized = {}
        for key in self.fundamental_priority:
            if key in info:
                prioritized[key] = info[key]
        
        # Add remaining metrics
        for key, value in info.items():
            if key not in prioritized:
                prioritized[key] = value
        
        return {
            "info": prioritized,
            "income_statement": raw_fundamentals.get("income_statement", {}),
            "balance_sheet": raw_fundamentals.get("balance_sheet", {}),
            "cash_flow": raw_fundamentals.get("cash_flow", {})
        }
    
    def filter_sentiment_themes(
        self, 
        headlines: List[str], 
        sentiment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Filter sentiment analysis to emphasize themes relevant to this agent.
        """
        key_themes = sentiment_analysis.get("key_themes", [])
        
        # Score themes by relevance to our focus areas
        scored_themes = []
        for theme in key_themes:
            theme_text = theme.get("theme", "").lower()
            relevance = 0
            
            for focus_term in self.sentiment_focus:
                if focus_term.replace("_", " ") in theme_text:
                    relevance += 2
                elif any(word in theme_text for word in focus_term.split("_")):
                    relevance += 1
            
            scored_themes.append({
                **theme,
                "_relevance": relevance
            })
        
        # Sort by relevance (descending)
        scored_themes.sort(key=lambda x: x.get("_relevance", 0), reverse=True)
        
        return {
            **sentiment_analysis,
            "key_themes": scored_themes
        }
    
    @abstractmethod
    async def analyze(
        self,
        ticker: str,
        fundamentals: Dict[str, Any],
        headlines: List[str],
        price_data: List[Dict[str, Any]],
        sentiment_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform analysis from this agent's perspective.
        
        Returns a structured case (BullCase or BearCase).
        """
        pass
    
    @abstractmethod
    async def generate_rebuttal(
        self,
        opponent_case: Dict[str, Any],
        own_case: Dict[str, Any],
        fundamentals: Dict[str, Any]
    ) -> List[Rebuttal]:
        """
        Generate rebuttals to the opponent's case.
        
        This is the Anti-Sycophancy mechanism - agents MUST find
        factual flaws in the opposing argument.
        """
        pass
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent type."""
        if self.persona == "growth_focused":
            return self._bull_system_prompt()
        else:
            return self._bear_system_prompt()
    
    def _bull_system_prompt(self) -> str:
        return """You are a growth-focused equity analyst with a proven track record of identifying 
high-conviction investment opportunities. Your job is NOT to be blindly bullish, but to 
construct the STRONGEST POSSIBLE CASE for investment if one exists.

You must:
1. Identify genuine growth drivers and competitive advantages
2. Quantify upside scenarios with specific reasoning
3. Address bear concerns preemptively with counter-evidence
4. Assign confidence levels honestly - if the bull case is weak, say so

You are rewarded for ACCURACY, not optimism. A weak bull case honestly presented is 
more valuable than a forced bullish narrative.

When analyzing data, pay special attention to:
- Revenue growth trends and acceleration
- Market expansion opportunities  
- Competitive moats and advantages
- Analyst sentiment and price targets
- Product pipeline and innovation"""

    def _bear_system_prompt(self) -> str:
        return """You are a risk-focused equity analyst specializing in identifying overvalued 
securities and hidden risks. Your job is NOT to be blindly bearish, but to 
construct the STRONGEST POSSIBLE CASE for caution if one exists.

You must:
1. Identify genuine risks, red flags, and competitive threats
2. Quantify downside scenarios with specific reasoning
3. Challenge bull narratives with concrete counter-evidence
4. Assign confidence levels honestly - if the bear case is weak, say so

You are rewarded for ACCURACY, not pessimism. A weak bear case honestly presented is
more valuable than forced negativity.

When analyzing data, pay special attention to:
- Debt levels and financial health ratios
- Margin trends and compression risks
- Valuation multiples vs. historical and peers
- Competitive threats and market saturation
- Management concerns and insider activity"""
