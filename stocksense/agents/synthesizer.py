"""
Synthesizer Agent

Impartial judge that weighs Bull and Bear cases,
cross-examines claims against evidence, and produces
a probability-weighted verdict.

Implements the Evidence Grader protocol to prevent sycophancy.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import uuid

from ..config import get_chat_llm, ConfigurationError

logger = logging.getLogger("stocksense.agents.synthesizer")


@dataclass
class EvidenceGrade:
    """Evaluation of how well a claim is supported by data."""
    claim: str
    source_agent: str  # "bull" or "bear"
    has_counter_evidence: bool
    data_support_score: float  # 0.0-1.0 how well data supports this
    rebuttal_strength: float  # 0.0-1.0 how strong was the opposing rebuttal
    final_credibility: float  # 0.0-1.0 overall credibility after cross-examination


@dataclass
class SynthesizedVerdict:
    """
    The final verdict synthesizing Bull and Bear perspectives.
    
    Designed for compatibility with Stage 4 (Watchman) thesis integration.
    """
    # Identification
    ticker: str
    analysis_id: str  # UUID for linking to AnalysisCache and theses
    timestamp: str
    
    # Scenario Probabilities (must sum to ~1.0)
    bull_probability: float  # P(bull case materializes)
    base_probability: float  # P(nothing dramatic happens)
    bear_probability: float  # P(bear case materializes)
    
    # Verdict
    recommendation: str  # "Strong Buy" | "Buy" | "Hold" | "Sell" | "Strong Sell"
    conviction: float  # 0.0-1.0
    
    # Analysis Quality Assessment
    bull_argument_strength: float  # How well-supported is the bull case?
    bear_argument_strength: float  # How well-supported is the bear case?
    
    # Evidence Grades
    evidence_grades: List[EvidenceGrade]
    
    # Key Decision Factors
    decisive_factors: List[str]  # What tipped the balance?
    unresolved_questions: List[str]  # What we still don't know
    
    # The Debate Summary
    bull_summary: str
    bear_summary: str
    synthesis_reasoning: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticker": self.ticker,
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "scenario_probabilities": {
                "bull": self.bull_probability,
                "base": self.base_probability,
                "bear": self.bear_probability
            },
            "recommendation": self.recommendation,
            "conviction": self.conviction,
            "argument_strength": {
                "bull": self.bull_argument_strength,
                "bear": self.bear_argument_strength
            },
            "evidence_grades": [
                {
                    "claim": eg.claim,
                    "source_agent": eg.source_agent,
                    "has_counter_evidence": eg.has_counter_evidence,
                    "data_support_score": eg.data_support_score,
                    "rebuttal_strength": eg.rebuttal_strength,
                    "final_credibility": eg.final_credibility
                }
                for eg in self.evidence_grades
            ],
            "decisive_factors": self.decisive_factors,
            "unresolved_questions": self.unresolved_questions,
            "debate_summary": {
                "bull": self.bull_summary,
                "bear": self.bear_summary,
                "synthesis": self.synthesis_reasoning
            }
        }
    
    def to_analysis_snapshot(self) -> Dict[str, Any]:
        """
        Convert to format compatible with origin_analysis_snapshot in theses table.
        
        This enables Stage 4 (Watchman) integration.
        """
        return {
            "verdict_type": "adversarial_debate",
            "recommendation": self.recommendation,
            "conviction": self.conviction,
            "scenario_probabilities": {
                "bull": self.bull_probability,
                "base": self.base_probability,
                "bear": self.bear_probability
            },
            "decisive_factors": self.decisive_factors,
            "analysis_id": self.analysis_id,
            "timestamp": self.timestamp,
            "bull_summary": self.bull_summary,
            "bear_summary": self.bear_summary
        }


class Synthesizer:
    """
    Impartial judge that synthesizes Bull and Bear cases.
    
    Implements the Evidence Grader protocol:
    1. Grade each claim against available data
    2. Check if claims have valid counter-evidence
    3. Weight arguments by evidence quality, not just confidence
    4. Produce probability-weighted scenario analysis
    """
    
    def __init__(self):
        try:
            self.llm = get_chat_llm(temperature=0.1)  # Lower temp for more consistent judgment
        except ConfigurationError as e:
            logger.warning(f"LLM not available for Synthesizer: {e}")
            self.llm = None
    
    async def synthesize(
        self,
        ticker: str,
        bull_case: Dict[str, Any],
        bear_case: Dict[str, Any],
        bull_rebuttals: List[Dict[str, Any]],
        bear_rebuttals: List[Dict[str, Any]],
        fundamentals: Dict[str, Any]
    ) -> SynthesizedVerdict:
        """
        Synthesize Bull and Bear cases into a final verdict.
        
        Uses the Evidence Grader protocol for cross-examination.
        """
        analysis_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        if not self.llm:
            return self._fallback_synthesis(ticker, bull_case, bear_case, analysis_id, timestamp)
        
        # Step 1: Grade evidence for both cases
        evidence_grades = await self._grade_evidence(
            bull_case, bear_case, bull_rebuttals, bear_rebuttals, fundamentals
        )
        
        # Step 2: Calculate argument strengths based on evidence
        bull_strength = self._calculate_argument_strength(evidence_grades, "bull")
        bear_strength = self._calculate_argument_strength(evidence_grades, "bear")
        
        # Step 3: Generate synthesis via LLM
        synthesis = await self._generate_synthesis(
            ticker, bull_case, bear_case, bull_rebuttals, bear_rebuttals,
            evidence_grades, bull_strength, bear_strength
        )
        
        return SynthesizedVerdict(
            ticker=ticker,
            analysis_id=analysis_id,
            timestamp=timestamp,
            bull_probability=synthesis.get("bull_probability", 0.33),
            base_probability=synthesis.get("base_probability", 0.34),
            bear_probability=synthesis.get("bear_probability", 0.33),
            recommendation=synthesis.get("recommendation", "Hold"),
            conviction=synthesis.get("conviction", 0.5),
            bull_argument_strength=bull_strength,
            bear_argument_strength=bear_strength,
            evidence_grades=evidence_grades,
            decisive_factors=synthesis.get("decisive_factors", []),
            unresolved_questions=synthesis.get("unresolved_questions", []),
            bull_summary=bull_case.get("thesis", ""),
            bear_summary=bear_case.get("thesis", ""),
            synthesis_reasoning=synthesis.get("reasoning", "")
        )
    
    async def _grade_evidence(
        self,
        bull_case: Dict[str, Any],
        bear_case: Dict[str, Any],
        bull_rebuttals: List[Dict[str, Any]],
        bear_rebuttals: List[Dict[str, Any]],
        fundamentals: Dict[str, Any]
    ) -> List[EvidenceGrade]:
        """
        Grade each claim against data and rebuttals.
        
        This is the core of the Anti-Sycophancy protocol.
        """
        grades = []
        
        # Grade Bull claims
        bull_claims = bull_case.get("key_claims", [])
        for claim in bull_claims:
            # Find if Bear has a rebuttal for this claim
            rebuttal = self._find_matching_rebuttal(claim, bear_rebuttals)
            
            grades.append(EvidenceGrade(
                claim=claim.get("statement", ""),
                source_agent="bull",
                has_counter_evidence=rebuttal is not None,
                data_support_score=float(claim.get("confidence", 0.5)),
                rebuttal_strength=float(rebuttal.get("strength", 0) if rebuttal else 0),
                final_credibility=self._calculate_credibility(
                    claim.get("confidence", 0.5),
                    rebuttal.get("strength", 0) if rebuttal else 0
                )
            ))
        
        # Grade Bear claims
        bear_claims = bear_case.get("key_claims", [])
        for claim in bear_claims:
            # Find if Bull has a rebuttal for this claim
            rebuttal = self._find_matching_rebuttal(claim, bull_rebuttals)
            
            grades.append(EvidenceGrade(
                claim=claim.get("statement", ""),
                source_agent="bear",
                has_counter_evidence=rebuttal is not None,
                data_support_score=float(claim.get("confidence", 0.5)),
                rebuttal_strength=float(rebuttal.get("strength", 0) if rebuttal else 0),
                final_credibility=self._calculate_credibility(
                    claim.get("confidence", 0.5),
                    rebuttal.get("strength", 0) if rebuttal else 0
                )
            ))
        
        return grades
    
    def _find_matching_rebuttal(
        self, 
        claim: Dict[str, Any], 
        rebuttals: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find a rebuttal that targets this claim."""
        claim_text = claim.get("statement", "").lower()
        
        for rebuttal in rebuttals:
            target = rebuttal.get("target_claim", "").lower()
            # Simple matching - in production, use semantic similarity
            if any(word in target for word in claim_text.split()[:3]):
                return rebuttal
        
        return None
    
    def _calculate_credibility(self, claim_confidence: float, rebuttal_strength: float) -> float:
        """
        Calculate final credibility of a claim after considering rebuttals.
        
        Formula: credibility = claim_confidence * (1 - rebuttal_strength * 0.5)
        """
        return claim_confidence * (1 - rebuttal_strength * 0.5)
    
    def _calculate_argument_strength(
        self, 
        grades: List[EvidenceGrade], 
        source: str
    ) -> float:
        """Calculate overall argument strength for an agent."""
        agent_grades = [g for g in grades if g.source_agent == source]
        
        if not agent_grades:
            return 0.5
        
        return sum(g.final_credibility for g in agent_grades) / len(agent_grades)
    
    async def _generate_synthesis(
        self,
        ticker: str,
        bull_case: Dict[str, Any],
        bear_case: Dict[str, Any],
        bull_rebuttals: List[Dict[str, Any]],
        bear_rebuttals: List[Dict[str, Any]],
        evidence_grades: List[EvidenceGrade],
        bull_strength: float,
        bear_strength: float
    ) -> Dict[str, Any]:
        """Generate the final synthesis via LLM."""
        
        prompt = f"""You are a senior portfolio manager evaluating two analyst reports.

TICKER: {ticker}

BULL CASE (Strength: {bull_strength:.2f}):
Thesis: {bull_case.get("thesis", "")}
Key Claims: {json.dumps(bull_case.get("key_claims", [])[:3], indent=2)}
Confidence: {bull_case.get("confidence", 0.5)}

BEAR CASE (Strength: {bear_strength:.2f}):
Thesis: {bear_case.get("thesis", "")}
Key Claims: {json.dumps(bear_case.get("key_claims", [])[:3], indent=2)}
Confidence: {bear_case.get("confidence", 0.5)}

BEAR'S REBUTTALS TO BULL:
{json.dumps(bear_rebuttals[:3], indent=2)}

BULL'S REBUTTALS TO BEAR:
{json.dumps(bull_rebuttals[:3], indent=2)}

EVIDENCE GRADES:
Bull Average Credibility: {bull_strength:.2f}
Bear Average Credibility: {bear_strength:.2f}

Your task:
1. Evaluate the QUALITY of arguments, not just conclusions
2. Identify which points are well-supported by data vs. speculation
3. Produce probability-weighted scenario analysis
4. Give a final recommendation with clear conviction level

Return a JSON object:
{{
  "bull_probability": 0.0-1.0,
  "base_probability": 0.0-1.0,
  "bear_probability": 0.0-1.0,
  "recommendation": "Strong Buy|Buy|Hold|Sell|Strong Sell",
  "conviction": 0.0-1.0,
  "decisive_factors": ["Factor 1", "Factor 2", "..."],
  "unresolved_questions": ["Question 1", "..."],
  "reasoning": "2-3 sentence synthesis of your decision"
}}

The three probabilities should sum to approximately 1.0.
Return ONLY the JSON object."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Synthesis generation failed: {e}")
            return {
                "bull_probability": 0.33,
                "base_probability": 0.34,
                "bear_probability": 0.33,
                "recommendation": "Hold",
                "conviction": 0.5,
                "decisive_factors": ["LLM synthesis failed"],
                "unresolved_questions": ["Full analysis unavailable"],
                "reasoning": "Unable to generate synthesis - manual review required."
            }
    
    def _fallback_synthesis(
        self,
        ticker: str,
        bull_case: Dict[str, Any],
        bear_case: Dict[str, Any],
        analysis_id: str,
        timestamp: str
    ) -> SynthesizedVerdict:
        """Fallback synthesis when LLM is unavailable."""
        return SynthesizedVerdict(
            ticker=ticker,
            analysis_id=analysis_id,
            timestamp=timestamp,
            bull_probability=0.33,
            base_probability=0.34,
            bear_probability=0.33,
            recommendation="Hold",
            conviction=0.3,
            bull_argument_strength=0.5,
            bear_argument_strength=0.5,
            evidence_grades=[],
            decisive_factors=["LLM unavailable - manual review required"],
            unresolved_questions=["Full AI analysis unavailable"],
            bull_summary=bull_case.get("thesis", ""),
            bear_summary=bear_case.get("thesis", ""),
            synthesis_reasoning="Automated synthesis unavailable. Please review Bull and Bear cases manually."
        )
