export type ThesisCheckEventType =
  | 'started'
  | 'source_started'
  | 'source_completed'
  | 'memory_completed'
  | 'preflight_completed'
  | 'evaluation_started'
  | 'evaluation_completed'
  | 'synthesis_started'
  | 'completed'
  | 'cancelled'
  | 'error';

export type SourceRunStatus = 'pending' | 'ok' | 'empty' | 'failed' | 'timeout' | 'skipped';
export type SourceType = 'news' | 'price' | 'fundamentals' | 'cached_analysis' | 'prior_run' | 'alert_history';
export type ConvictionVerdict = 'hold' | 'revise' | 'monitor' | 'invalidate' | 'insufficient_evidence';
export type ConfidenceBand = 'low' | 'medium' | 'high';

export interface SourceStatus {
  source_type: SourceType;
  status: SourceRunStatus;
  latency_ms: number;
  error?: string | null;
}

export interface EvidenceItem {
  id?: string;
  local_id?: string | null;
  source_type: SourceType;
  source_name: string;
  title: string;
  text: string;
  url?: string | null;
  published_at?: string | null;
  reliability_tier: 'high' | 'medium' | 'low';
  evidence_hash?: string;
  metadata?: Record<string, unknown>;
}

export interface MemorySnapshot {
  prior_run_found: boolean;
  prior_alerts_count: number;
  thesis_history_count: number;
  latest_cached_analysis_found: boolean;
  latest_prior_run_id?: string | null;
  latest_prior_verdict?: string | null;
  latest_prior_evidence_hash?: string | null;
  latest_prior_thesis_hash?: string | null;
  user_corrections: string[];
  notable_prior_changes: string[];
}

export interface ClaimAssessment {
  claim: string;
  stance: 'supports' | 'weakens' | 'contradicts' | 'unsupported';
  confidence: ConfidenceBand;
  evidence_refs: string[];
  rationale: string;
}

export interface AdversarialEvaluation {
  support: string[];
  opposition: string[];
  contradictions: string[];
  missing_evidence: string[];
  human_review_items: string[];
  claim_assessments: ClaimAssessment[];
}

export interface ConvictionDiff {
  verdict: ConvictionVerdict;
  confidence: ConfidenceBand;
  strengthened_claims: string[];
  weakened_claims: string[];
  broken_claims: string[];
  unsupported_claims: string[];
  summary: string;
  next_actions: string[];
  claim_assessments: ClaimAssessment[];
}

export interface ThesisCheckFinal {
  run_id: string;
  thesis_id: string;
  ticker: string;
  evidence_hash: string;
  memory: MemorySnapshot;
  evaluation: AdversarialEvaluation;
  conviction: ConvictionDiff;
  source_statuses: SourceStatus[];
  cache_hit: boolean;
  run_mode: string;
  thesis_hash?: string | null;
}

export interface ThesisCheckStreamEvent {
  type: ThesisCheckEventType;
  run_id: string;
  thesis_id: string;
  ticker: string;
  phase: string;
  progress: number;
  message: string;
  data: Record<string, unknown>;
}

export interface ThesisCheckRunRecord {
  id: string;
  user_id: string;
  thesis_id: string;
  ticker: string;
  status: string;
  run_mode?: string;
  idempotency_key?: string | null;
  thesis_hash?: string | null;
  evidence_hash?: string | null;
  cache_hit?: boolean;
  final_verdict?: string | null;
  final_confidence?: string | null;
  final_summary?: string | null;
  final_result?: ThesisCheckFinal | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface ThesisCheckStepRecord {
  id: string;
  run_id: string;
  step_name: string;
  status: string;
  latency_ms: number;
  data: Record<string, unknown>;
  error_message?: string | null;
  retry_count?: number;
  model?: string | null;
  prompt_version?: string | null;
  input_token_estimate?: number | null;
  output_token_estimate?: number | null;
  cost_estimate_usd?: number | null;
  validation_errors?: string[];
  created_at: string;
}

export interface ThesisCheckRunBundle {
  run: ThesisCheckRunRecord | null;
  steps: ThesisCheckStepRecord[];
  evidence: EvidenceItem[];
}

export interface ThesisCorrectionRequest {
  correction_type: string;
  correction_text?: string | null;
  claim?: string | null;
  evidence_local_id?: string | null;
}
