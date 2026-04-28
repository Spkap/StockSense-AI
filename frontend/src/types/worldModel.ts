export type ClaimType = 'growth' | 'margin' | 'competitive' | 'valuation' | 'execution' | 'risk' | 'capital_allocation';
export type ClaimStatus = 'active' | 'watching' | 'validated' | 'invalidated';
export type ConfidenceBand = 'low' | 'medium' | 'high';
export type ScenarioName = 'bull' | 'base' | 'bear';

export interface ClaimObservable {
  observable_name: string;
  source_type: string;
  metric_key?: string | null;
  threshold_operator?: '>' | '>=' | '<' | '<=' | '=' | '!=' | null;
  threshold_value?: number | null;
  period?: string | null;
}

export interface ThesisClaim {
  id?: string | null;
  claim_text: string;
  claim_type: ClaimType;
  metric_hint?: string | null;
  time_horizon?: string | null;
  status: ClaimStatus;
  confidence: ConfidenceBand;
  evidence_needed: string[];
  observables: ClaimObservable[];
}

export interface ForecastQuestion {
  id?: string | null;
  claim_id?: string | null;
  question: string;
  resolution_criteria: string;
  due_date?: string | null;
  probability?: number | null;
  status: 'open' | 'resolved';
  resolved_outcome?: boolean | null;
  brier_score?: number | null;
}

export interface FalsifiabilityCompileResult {
  thesis_id: string;
  ticker: string;
  claims: ThesisClaim[];
  forecast_questions: ForecastQuestion[];
  kill_criteria: string[];
}

export interface ScenarioPath {
  scenario: ScenarioName;
  summary: string;
  driver_changes: string[];
  impacted_claims: string[];
  evidence_required: string[];
  confidence: ConfidenceBand;
}

export interface ScenarioBoardResult {
  thesis_id: string;
  ticker: string;
  scenarios: ScenarioPath[];
}
