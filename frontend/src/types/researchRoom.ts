export type RunEventType =
  | 'started'
  | 'plan_started'
  | 'plan_completed'
  | 'source_started'
  | 'source_completed'
  | 'index_completed'
  | 'retrieval_completed'
  | 'agent_started'
  | 'agent_completed'
  | 'referee_completed'
  | 'memo_completed'
  | 'completed'
  | 'cancelled'
  | 'error';

export type RunStatus = 'queued' | 'running' | 'completed' | 'completed_cached' | 'failed' | 'cancelled';
export type ResearchSourceType = 'sec_filing' | 'sec_company_facts' | 'price' | 'fundamentals' | 'news' | 'retrieval' | 'prior_run' | 'manual';
export type ResearchSourceStatusType = 'sec_submissions' | 'sec_company_facts' | 'price' | 'fundamentals' | 'news';
export type SourceRunStatus = 'pending' | 'ok' | 'empty' | 'failed' | 'timeout' | 'skipped';
export type NarrativeVerdict = 'supported' | 'weakened' | 'contradicted' | 'mixed' | 'unsupported' | 'insufficient_evidence';
export type ClaimStance = 'supports' | 'weakens' | 'contradicts' | 'unsupported';
export type ConfidenceBand = 'low' | 'medium' | 'high';

export interface RunStreamEvent {
  type: RunEventType;
  run_id: string;
  run_type: 'research_room';
  ticker?: string | null;
  phase: string;
  progress: number;
  message: string;
  data: Record<string, unknown>;
}

export interface SourceStatus {
  source_type: ResearchSourceStatusType;
  status: SourceRunStatus;
  latency_ms: number;
  error?: string | null;
}

export interface ResearchEvidenceItem {
  local_id: string;
  source_type: ResearchSourceType;
  source_name: string;
  title: string;
  text: string;
  url?: string | null;
  published_at?: string | null;
  accession_number?: string | null;
  filing_type?: string | null;
  metric_name?: string | null;
  metric_value?: string | number | null;
  period?: string | null;
  reliability_tier: 'high' | 'medium' | 'low';
  metadata: Record<string, unknown>;
}

export interface MetricEvidence {
  metric: string;
  value: string | number;
  period?: string | null;
  evidence_refs: string[];
  interpretation: string;
}

export interface ClaimAssessment {
  claim: string;
  stance: ClaimStance;
  confidence: ConfidenceBand;
  evidence_refs: string[];
  rationale: string;
}

export interface NarrativeTruthTest {
  verdict: NarrativeVerdict;
  confidence: ConfidenceBand;
  answer: string;
  supported: ClaimAssessment[];
  weakened: ClaimAssessment[];
  contradicted: ClaimAssessment[];
  missing_proof: string[];
  next_watch_items: string[];
}

export interface ContradictionCard {
  title: string;
  contradiction: string;
  severity: 'low' | 'medium' | 'high';
  evidence_refs: string[];
  why_it_matters: string;
}

export interface ResearchMemo {
  verdict: NarrativeVerdict;
  executive_summary: string;
  supported_points: string[];
  weakened_points: string[];
  missing_proof: string[];
  next_watch_items: string[];
}

export interface ResearchThesisDraft {
  ticker: string;
  thesis_summary: string;
  conviction_level: ConfidenceBand;
  kill_criteria: string[];
  time_horizon: 'short' | 'medium' | 'long';
  thesis_type: 'growth' | 'value' | 'income' | 'turnaround' | 'special_situation';
  evidence_refs: string[];
}

export interface ResearchRoomFinal {
  run_id: string;
  ticker: string;
  question: string;
  company_snapshot: Record<string, unknown>;
  narrative_test: NarrativeTruthTest;
  key_metrics: MetricEvidence[];
  contradiction_cards: ContradictionCard[];
  bull_case: ClaimAssessment[];
  bear_case: ClaimAssessment[];
  evidence: ResearchEvidenceItem[];
  memo: ResearchMemo;
  thesis_draft: ResearchThesisDraft;
  source_statuses: SourceStatus[];
}

export interface ResearchRoomRunBundle {
  run: {
    id: string;
    user_id: string;
    run_type: 'research_room';
    status: RunStatus;
    ticker?: string | null;
    question?: string | null;
    final_result?: ResearchRoomFinal | null;
    created_at?: string;
    completed_at?: string | null;
  } | null;
  steps: Array<Record<string, unknown>>;
}
