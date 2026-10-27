import axios, { AxiosError, AxiosInstance } from 'axios';
import type { AnalysisResponse, CachedTickersResponse, HealthResponse } from '../types/api';
import { API_BASE_URL } from '../config/env';
import { supabase } from '../utils/supabase';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for long-running analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

async function researchHeaders(owner: string | null) {
  const { data: { session }, error } = supabase ? await supabase.auth.getSession() : { data: { session: null }, error: null };
  if (error || (session?.user.id || null) !== owner) throw new Error('Your session changed. Please try again.');
  return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
}

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const rawDetail = (error.response.data as { detail?: unknown })?.detail;
      const detail = typeof rawDetail === 'string' ? rawDetail : 'The request could not be completed. Please try again.';
      
      if (status === 404) {
        throw new Error(detail);
      } else if (status === 401) {
        throw new Error('Please sign in again to continue.');
      } else if (status === 403) {
        throw new Error('You do not have access to this action.');
      } else if (status === 429) {
        throw new Error('Rate limit exceeded. Please try again later.');
      } else if (status >= 500) {
        throw new Error('The service is temporarily unavailable. Please try again.');
      }
      throw new Error(detail);
    } else if (error.request) {
      // Request made but no response
      throw new Error('Could not connect to StockSense. Check your connection and try again.');
    }
    throw error;
  }
);

// API functions
export const api = {
  // Health check
  async checkHealth(): Promise<HealthResponse> {
    const { data } = await apiClient.get<HealthResponse>('/health');
    return data;
  },

  // Analyze a stock ticker (optionally with auth for kill criteria monitoring)
  async analyzeStock(ticker: string, force: boolean = false, accessToken?: string): Promise<AnalysisResponse> {
    const params = force ? { force: 'true' } : {};
    const headers: Record<string, string> = {};
    
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }
    
    const { data } = await apiClient.post<AnalysisResponse>(
      `/analyze/${ticker.toUpperCase()}`,
      null,
      { params, headers }
    );
    return data;
  },

  // Get cached analysis results
  async getResults(ticker: string, owner: string | null): Promise<AnalysisResponse> {
    const { data } = await apiClient.get<AnalysisResponse>(`/results/${ticker.toUpperCase()}`, { headers: await researchHeaders(owner) });
    return data;
  },

  // Get list of cached tickers
  async getCachedTickers(owner: string | null): Promise<CachedTickersResponse> {
    const { data } = await apiClient.get<CachedTickersResponse>('/cached-tickers', { headers: await researchHeaders(owner) });
    return data;
  },

  // Delete cached analysis
  async deleteAnalysis(ticker: string, owner: string | null): Promise<{ message: string; ticker: string }> {
    const { data } = await apiClient.delete<{ message: string; ticker: string }>(
      `/results/${ticker.toUpperCase()}`, { headers: await researchHeaders(owner) }
    );
    return data;
  },
};

export default api;
