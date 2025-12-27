/**
 * Phase 3: Adversarial Collaboration Types
 * TypeScript interfaces for the debate analysis system
 */

export interface Catalyst {
  description: string;
  timeframe: 'near-term' | 'medium-term' | 'long-term';
  probability: number;
  potential_impact: 'low' | 'medium' | 'high';
}

export interface Risk {
  description: string;
  category: 'financial' | 'competitive' | 'operational' | 'regulatory' | 'management';
  severity: 'low' | 'medium' | 'high' | 'critical';
  probability: number;
  timeframe: 'near-term' | 'medium-term' | 'long-term';
}

export interface Claim {
  statement: string;
  evidence: string;
  confidence: number;
  data_source: 'fundamentals' | 'news' | 'price';
}

export interface Rebuttal {
  target_claim: string;
  counter_argument: string;
  counter_evidence: string | null;
  strength: number;
}

export interface BullCase {
  ticker: string;
  thesis: string;
  catalysts: Catalyst[];
  key_metrics: Record<string, any>;
  upside_reasoning: string;
  confidence: number;
  weaknesses: string[];
  key_claims: Claim[];
}

export interface BearCase {
  ticker: string;
  thesis: string;
  risks: Risk[];
  red_flags: string[];
  key_metrics: Record<string, any>;
  downside_reasoning: string;
  confidence: number;
  what_would_make_bullish: string[];
  key_claims: Claim[];
}

export interface EvidenceGrade {
  claim: string;
  source_agent: 'bull' | 'bear';
  has_counter_evidence: boolean;
  data_support_score: number;
  rebuttal_strength: number;
  final_credibility: number;
}

export interface ScenarioProbabilities {
  bull: number;
  base: number;
  bear: number;
}

export interface Verdict {
  ticker: string;
  analysis_id: string;
  timestamp: string;
  scenario_probabilities: ScenarioProbabilities;
  recommendation: 'Strong Buy' | 'Buy' | 'Hold' | 'Sell' | 'Strong Sell';
  conviction: number;
  argument_strength: {
    bull: number;
    bear: number;
  };
  evidence_grades: EvidenceGrade[];
  decisive_factors: string[];
  unresolved_questions: string[];
  debate_summary: {
    bull: string;
    bear: string;
    synthesis: string;
  };
}

export interface Rebuttals {
  bear_to_bull: Rebuttal[];
  bull_to_bear: Rebuttal[];
}

export interface DebateAnalysisResult {
  ticker: string;
  analysis_type: 'adversarial_debate';
  verdict: Verdict;
  bull_case: BullCase;
  bear_case: BearCase;
  rebuttals: Rebuttals;
  fundamentals: Record<string, any> | null;
  headlines: string[] | null;
  timestamp: string;
  error: string | null;
}

export interface DebateAnalysisResponse {
  message: string;
  ticker: string;
  analysis_type: 'adversarial_debate';
  data: DebateAnalysisResult;
}

/**
 * Stage 4 Integration: Analysis snapshot format for theses
 */
export interface AnalysisSnapshot {
  verdict_type: 'adversarial_debate';
  recommendation: string;
  conviction: number;
  scenario_probabilities: ScenarioProbabilities;
  decisive_factors: string[];
  analysis_id: string;
  timestamp: string;
  bull_summary: string;
  bear_summary: string;
}
