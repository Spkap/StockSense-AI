/**
 * Thesis API client and React Query hooks
 * Stage 3: User Belief System
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { 
  Thesis, 
  ThesesResponse, 
  CreateThesisRequest, 
  UpdateThesisRequest,
  ThesisHistoryResponse,
  ThesisComparison
} from '../types/thesis';
import { createAuthenticatedClient } from './authenticated';
import { useAuth } from '../context/AuthContext';

// Query keys
export const thesisKeys = {
  all: (userId: string) => ['private', userId, 'theses'] as const,
  byTicker: (userId: string, ticker: string) => ['private', userId, 'theses', ticker.toUpperCase()] as const,
  history: (userId: string, thesisId: string) => ['private', userId, 'thesis-history', thesisId] as const,
  comparison: (userId: string, thesisId: string) => ['private', userId, 'thesis-comparison', thesisId] as const,
};

/**
 * Hook to fetch all user theses
 */
export function useTheses(ticker?: string, enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId
      ? ticker
        ? thesisKeys.byTicker(userId, ticker)
        : thesisKeys.all(userId)
      : ['private', 'anonymous', 'theses', ticker?.toUpperCase() ?? 'all'],
    queryFn: async () => {
      const client = await createThesisClient();
      const params = ticker ? { ticker: ticker.toUpperCase() } : {};
      const { data } = await client.get<ThesesResponse>('/api/theses', { params });
      return data;
    },
    staleTime: 1000 * 60 * 2, // 2 minutes
    enabled: enabled && !!userId,
  });
}

const createThesisClient = createAuthenticatedClient;

/**
 * Hook to check if user has thesis for a specific ticker
 */
export function useThesisForTicker(ticker: string | null, enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId
      ? thesisKeys.byTicker(userId, ticker || '')
      : ['private', 'anonymous', 'theses', ticker?.toUpperCase() ?? ''],
    queryFn: async () => {
      if (!ticker) return { theses: [], count: 0 };
      const client = await createThesisClient();
      const { data } = await client.get<ThesesResponse>('/api/theses', { 
        params: { ticker: ticker.toUpperCase() } 
      });
      return data;
    },
    enabled: !!ticker && enabled && !!userId,
    staleTime: 1000 * 60 * 2,
  });
}

/**
 * Hook to create a new thesis
 */
export function useCreateThesis() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: async (thesis: CreateThesisRequest) => {
      const client = await createThesisClient();
      const { data } = await client.post<Thesis>('/api/theses', thesis);
      return data;
    },
    onSuccess: (data) => {
      if (!userId) return;
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: thesisKeys.all(userId) });
      queryClient.invalidateQueries({ queryKey: thesisKeys.byTicker(userId, data.ticker) });
    },
  });
}

/**
 * Hook to update a thesis
 */
export function useUpdateThesis() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: async ({ thesisId, updates }: { thesisId: string; updates: UpdateThesisRequest }) => {
      const client = await createThesisClient();
      const { data } = await client.patch<Thesis>(`/api/theses/${thesisId}`, updates);
      return data;
    },
    onSuccess: (data) => {
      if (!userId) return;
      queryClient.invalidateQueries({ queryKey: thesisKeys.all(userId) });
      queryClient.invalidateQueries({ queryKey: thesisKeys.byTicker(userId, data.ticker) });
    },
  });
}

/**
 * Hook to get thesis history
 */
export function useThesisHistory(thesisId: string | null, enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId
      ? thesisKeys.history(userId, thesisId || '')
      : ['private', 'anonymous', 'thesis-history', thesisId ?? ''],
    queryFn: async () => {
      if (!thesisId) return { history: [], count: 0 };
      const client = await createThesisClient();
      const { data } = await client.get<ThesisHistoryResponse>(`/api/theses/${thesisId}/history`);
      return data;
    },
    enabled: !!thesisId && enabled && !!userId,
  });
}

/**
 * Hook to compare thesis with current analysis (Stage 4)
 */
export function useThesisComparison(thesisId: string | null, enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId
      ? thesisKeys.comparison(userId, thesisId || '')
      : ['private', 'anonymous', 'thesis-comparison', thesisId ?? ''],
    queryFn: async () => {
      if (!thesisId) return null;
      const client = await createThesisClient();
      const { data } = await client.get<ThesisComparison>(`/api/theses/${thesisId}/compare`);
      return data;
    },
    enabled: !!thesisId && enabled && !!userId,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
