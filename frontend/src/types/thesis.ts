// TypeScript interfaces for Thesis data (Stage 3: User Belief System)

/**
 * Analysis snapshot stored with thesis at creation time
 */
export interface AnalysisSnapshot {
  sentiment: string;
  confidence: number;
  skeptic_verdict?: string;
  key_themes?: string[];
  timestamp: string;
}

/**
 * Thesis data returned from API
 */
export interface Thesis {
  id: string;
  ticker: string;
  thesis_summary: string;
  conviction_level: 'low' | 'medium' | 'high';
  kill_criteria: string[];
  time_horizon: 'short' | 'medium' | 'long';
  thesis_type: 'growth' | 'value' | 'income' | 'turnaround' | 'special_situation';
  status: 'active' | 'validated' | 'invalidated' | 'exited';
  // Stage 4: Analysis-Thesis Linkage
  origin_analysis_id?: number;
  origin_analysis_snapshot?: AnalysisSnapshot;
  created_at: string;
  updated_at: string;
}

/**
 * Thesis history entry
 */
export interface ThesisHistoryEntry {
  id: string;
  thesis_id: string;
  thesis_summary: string;
  conviction_level: string;
  kill_criteria: string[];
  change_type: 'created' | 'updated' | 'conviction_changed' | 'invalidated' | 'exited';
  change_reason?: string;
  created_at: string;
}

/**
 * Create thesis request
 */
export interface CreateThesisRequest {
  ticker: string;
  thesis_summary: string;
  conviction_level?: 'low' | 'medium' | 'high';
  kill_criteria?: string[];
  time_horizon?: 'short' | 'medium' | 'long';
  thesis_type?: 'growth' | 'value' | 'income' | 'turnaround' | 'special_situation';
  // Stage 4: Analysis-Thesis Linkage
  origin_analysis_id?: number;
  origin_analysis_snapshot?: AnalysisSnapshot;
}

/**
 * Update thesis request
 */
export interface UpdateThesisRequest {
  thesis_summary?: string;
  conviction_level?: 'low' | 'medium' | 'high';
  kill_criteria?: string[];
  status?: 'active' | 'validated' | 'invalidated' | 'exited';
  invalidation_reason?: string;
  change_reason?: string;
}

/**
 * Thesis comparison response (Stage 4)
 */
export interface ThesisComparisonChange {
  field: string;
  from: string | number;
  to: string | number;
  delta?: number;
  direction: 'changed' | 'increased' | 'decreased';
}

export interface ThesisComparison {
  has_comparison: boolean;
  thesis_id: string;
  ticker: string;
  message?: string;
  thesis_created_at?: string;
  origin?: AnalysisSnapshot;
  current?: {
    sentiment: string;
    confidence: number;
    timestamp: string;
  };
  changes?: ThesisComparisonChange[];
  change_summary?: string;
}

/**
 * API response wrappers
 */
export interface ThesesResponse {
  theses: Thesis[];
  count: number;
}

export interface ThesisHistoryResponse {
  history: ThesisHistoryEntry[];
  count: number;
}

