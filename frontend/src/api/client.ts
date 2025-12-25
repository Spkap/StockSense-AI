import axios, { AxiosError, AxiosInstance } from 'axios';
import type { AnalysisResponse, CachedTickersResponse, HealthResponse } from '../types/api';

// API base URL from environment or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

// Create axios instance with default config
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for long-running analysis
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const detail = (error.response.data as { detail?: string })?.detail || error.message;
      
      if (status === 404) {
        throw new Error(`Not found: ${detail}`);
      } else if (status === 429) {
        throw new Error('Rate limit exceeded. Please try again later.');
      } else if (status >= 500) {
        throw new Error(`Server error: ${detail}`);
      }
      throw new Error(detail);
    } else if (error.request) {
      // Request made but no response
      throw new Error('Unable to connect to server. Please check if the backend is running.');
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
  async getResults(ticker: string): Promise<AnalysisResponse> {
    const { data } = await apiClient.get<AnalysisResponse>(`/results/${ticker.toUpperCase()}`);
    return data;
  },

  // Get list of cached tickers
  async getCachedTickers(): Promise<CachedTickersResponse> {
    const { data } = await apiClient.get<CachedTickersResponse>('/cached-tickers');
    return data;
  },

  // Delete cached analysis
  async deleteAnalysis(ticker: string): Promise<{ message: string; ticker: string }> {
    const { data } = await apiClient.delete<{ message: string; ticker: string }>(
      `/results/${ticker.toUpperCase()}`
    );
    return data;
  },
};

export default api;
