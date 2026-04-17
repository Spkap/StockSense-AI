import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './client';
import { supabase } from '../utils/supabase';
import { API_BASE_URL } from '../config/env';
import type { KillAlert } from '../types/api';

// Query keys for cache management
export const queryKeys = {
  health: ['health'] as const,
  cachedTickers: ['cached-tickers'] as const,
  analysis: (ticker: string) => ['analysis', ticker.toUpperCase()] as const,
  results: (ticker: string) => ['results', ticker.toUpperCase()] as const,
};

/**
 * Hook to check backend health status
 */
export function useHealthCheck() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.checkHealth,
    refetchInterval: 30000, // Check every 30 seconds
    retry: false,
  });
}

/**
 * Hook to get list of cached tickers
 */
export function useCachedTickers() {
  return useQuery({
    queryKey: queryKeys.cachedTickers,
    queryFn: api.getCachedTickers,
  });
}

/**
 * Hook to get cached analysis results for a ticker
 */
export function useAnalysisResults(ticker: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: queryKeys.results(ticker || ''),
    queryFn: () => api.getResults(ticker!),
    enabled: !!ticker && enabled,
    retry: false,
  });
}

/**
 * Hook to trigger new stock analysis
 */
export function useAnalyzeStock() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticker, force = false, accessToken }: { ticker: string; force?: boolean; accessToken?: string }) => 
      api.analyzeStock(ticker, force, accessToken),
    onSuccess: (data) => {
      // Update the results cache with the new analysis
      queryClient.setQueryData(queryKeys.results(data.ticker), data);
      // Invalidate cached tickers list to include the new one
      queryClient.invalidateQueries({ queryKey: queryKeys.cachedTickers });
    },
  });
}

/**
 * Hook to fetch kill alerts for a ticker (authenticated users only)
 * Used to populate KillAlertBanner after streaming analysis completes.
 */
export function useKillAlerts(ticker: string | null) {
  return useQuery({
    queryKey: ['kill-alerts', ticker?.toUpperCase()],
    queryFn: async (): Promise<KillAlert[]> => {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session?.access_token || !ticker) return [];

      const resp = await fetch(
        `${API_BASE_URL}/api/kill-alerts?ticker=${ticker.toUpperCase()}&status=pending`,
        { headers: { Authorization: `Bearer ${session.access_token}` } }
      );
      if (!resp.ok) return [];
      const json = await resp.json();
      return (json.alerts ?? []) as KillAlert[];
    },
    enabled: !!ticker,
    staleTime: 0, // always fresh — we want new alerts immediately
  });
}

/**
 * Hook to delete cached analysis
 */
export function useDeleteAnalysis() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (ticker: string) => api.deleteAnalysis(ticker),
    onSuccess: (_, ticker) => {
      // Remove from results cache
      queryClient.removeQueries({ queryKey: queryKeys.results(ticker) });
      // Invalidate cached tickers list
      queryClient.invalidateQueries({ queryKey: queryKeys.cachedTickers });
    },
  });
}
