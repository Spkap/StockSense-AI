// TypeScript interfaces for Thesis data (Stage 3: User Belief System)

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
