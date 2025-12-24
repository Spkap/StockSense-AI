import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './client';

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
export function useAnalysisResults(ticker: string | null) {
  return useQuery({
    queryKey: queryKeys.results(ticker || ''),
    queryFn: () => api.getResults(ticker!),
    enabled: !!ticker,
  });
}

/**
 * Hook to trigger new stock analysis
 */
export function useAnalyzeStock() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ ticker, force = false }: { ticker: string; force?: boolean }) => 
      api.analyzeStock(ticker, force),
    onSuccess: (data) => {
      // Update the results cache with the new analysis
      queryClient.setQueryData(queryKeys.results(data.ticker), data);
      // Invalidate cached tickers list to include the new one
      queryClient.invalidateQueries({ queryKey: queryKeys.cachedTickers });
    },
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
