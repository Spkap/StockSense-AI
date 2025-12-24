// TypeScript interfaces for API responses
// Updated to match backend with full analysis data

/**
 * Individual price data point from OHLCV data
 */
export interface PriceDataPoint {
  Date: string;
  Open: number | null;
  High: number | null;
  Low: number | null;
  Close: number | null;
  Volume: number | null;
}

/**
 * Per-headline sentiment analysis (Stage 1: Epistemic Foundation)
 */
export interface HeadlineAnalysis {
  headline: string;
  sentiment: 'Bullish' | 'Bearish' | 'Neutral' | 'Insufficient Data';
  confidence: number; // 0.0 to 1.0
  reasoning: string;
  key_entities: string[];
}

/**
 * Recurring theme identified across headlines
 */
export interface KeyTheme {
  theme: string;
  sentiment_direction: 'Bullish' | 'Bearish' | 'Mixed' | 'Neutral';
  headline_count: number;
  summary: string;
}

/**
 * Skeptic critique (Stage 2: Visible Skepticism)
 */
export interface Critique {
  critique: string;
  assumption_challenged: string;
  evidence: string;
}

/**
 * Bear case scenario
 */
export interface BearCase {
  argument: string;
  trigger: string;
  severity: 'High' | 'Medium' | 'Low';
}

/**
 * Core analysis data returned by the API
 */
export interface AnalysisData {
  id?: number;
  ticker: string;
  summary: string;
  sentiment_report: string;
  price_data: PriceDataPoint[];
  headlines: string[];
  headlines_count: number;
  reasoning_steps: string[];
  tools_used: string[];
  iterations: number;
  timestamp: string;
  cache_age_hours?: number | null;
  source: 'cache' | 'react_analysis';
  agent_type: 'ReAct';
  // Structured sentiment analysis (Stage 1: Epistemic Foundation)
  overall_sentiment?: 'Bullish' | 'Bearish' | 'Neutral' | 'Insufficient Data' | '';
  overall_confidence?: number; // 0.0 to 1.0
  confidence_reasoning?: string;
  headline_analyses?: HeadlineAnalysis[];
  key_themes?: KeyTheme[];
  potential_impact?: 'Strong Positive' | 'Moderate Positive' | 'Minimal' | 'Moderate Negative' | 'Strong Negative' | 'Uncertain' | '';
  risks_identified?: string[];
  information_gaps?: string[];
  // Skeptic analysis (Stage 2: Visible Skepticism)
  skeptic_report?: string;
  skeptic_sentiment?: 'Disagree' | 'Partially Disagree' | 'Agree with Reservations' | 'Agree' | '';
  skeptic_confidence?: number;
  primary_disagreement?: string;
  critiques?: Critique[];
  bear_cases?: BearCase[];
  hidden_risks?: string[];
  would_change_mind?: string[];
}

/**
 * Full API response wrapper for /analyze and /results endpoints
 */
export interface AnalysisResponse {
  message: string;
  ticker: string;
  data: AnalysisData;
}

/**
 * Cached ticker item with timestamp
 */
export interface CachedTickerItem {
  symbol: string;
  timestamp: string | null;
}

/**
 * Response from /cached-tickers endpoint
 */
export interface CachedTickersResponse {
  message: string;
  count: number;
  tickers: CachedTickerItem[];
}

/**
 * Health check response with detailed status
 */
export interface HealthCheckStatus {
  status: 'ok' | 'error';
  message?: string;
  cached_analyses?: number;
}

export interface HealthResponse {
  status: 'ok' | 'degraded' | string;
  timestamp: string;
  version: string;
  checks: {
    google_api_key: HealthCheckStatus;
    newsapi_key: HealthCheckStatus;
    database: HealthCheckStatus;
  };
}

/**
 * Delete response
 */
export interface DeleteResponse {
  message: string;
  ticker: string;
}
