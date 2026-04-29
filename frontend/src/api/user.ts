import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type {
  CreatePositionRequest,
  KillAlert,
  KillAlertsResponse,
  KillAlertStatus,
  KillAlertStatusUpdate,
  Position,
  PositionsResponse,
  UserProfile,
} from '../types/api';
import { createAuthenticatedClient } from './authenticated';
import { useAuth } from '../context/AuthContext';

export const userKeys = {
  profile: (userId: string) => ['private', userId, 'profile'] as const,
  positions: (userId: string) => ['private', userId, 'positions'] as const,
  alerts: (userId: string, status: string, ticker?: string | null) => ['private', userId, 'kill-alerts', status, ticker?.toUpperCase() ?? 'all'] as const,
  alert: (userId: string, alertId: string | null) => ['private', userId, 'kill-alert', alertId] as const,
};

async function fetchProfile(): Promise<UserProfile> {
  const client = await createAuthenticatedClient();
  const { data } = await client.get<UserProfile>('/api/me');
  return data;
}

async function fetchPositions(): Promise<PositionsResponse> {
  const client = await createAuthenticatedClient();
  const { data } = await client.get<PositionsResponse>('/api/positions');
  return data;
}

async function createPosition(position: CreatePositionRequest): Promise<Position> {
  const client = await createAuthenticatedClient();
  const { data } = await client.post<Position>('/api/positions', position);
  return data;
}

async function deletePosition(positionId: string): Promise<{ message: string }> {
  const client = await createAuthenticatedClient();
  const { data } = await client.delete<{ message: string }>(`/api/positions/${positionId}`);
  return data;
}

async function fetchKillAlerts({
  status = 'pending',
  ticker,
}: {
  status?: KillAlertStatus | 'all';
  ticker?: string | null;
}): Promise<KillAlertsResponse> {
  const client = await createAuthenticatedClient();
  const params: Record<string, string> = { status };
  if (ticker) {
    params.ticker = ticker.toUpperCase();
  }
  const { data } = await client.get<KillAlertsResponse>('/api/kill-alerts', { params });
  return data;
}

async function fetchKillAlert(alertId: string): Promise<KillAlert> {
  const client = await createAuthenticatedClient();
  const { data } = await client.get<KillAlert>(`/api/kill-alerts/${alertId}`);
  return data;
}

async function updateKillAlert({
  alertId,
  update,
}: {
  alertId: string;
  update: KillAlertStatusUpdate;
}): Promise<{ message: string; status: string }> {
  const client = await createAuthenticatedClient();
  const { data } = await client.patch<{ message: string; status: string }>(`/api/kill-alerts/${alertId}`, update);
  return data;
}

async function deleteKillAlert(alertId: string): Promise<{ message: string }> {
  const client = await createAuthenticatedClient();
  const { data } = await client.delete<{ message: string }>(`/api/kill-alerts/${alertId}`);
  return data;
}

export function useBackendProfile(enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId ? userKeys.profile(userId) : ['private', 'anonymous', 'profile'],
    queryFn: fetchProfile,
    enabled: enabled && !!userId,
    retry: false,
  });
}

export function usePositions(enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId ? userKeys.positions(userId) : ['private', 'anonymous', 'positions'],
    queryFn: fetchPositions,
    enabled: enabled && !!userId,
    retry: false,
  });
}

export function useCreatePosition() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: createPosition,
    onSuccess: () => {
      if (userId) {
        queryClient.invalidateQueries({ queryKey: userKeys.positions(userId) });
      }
    },
  });
}

export function useDeletePosition() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: deletePosition,
    onSuccess: () => {
      if (userId) {
        queryClient.invalidateQueries({ queryKey: userKeys.positions(userId) });
      }
    },
  });
}

export function useKillAlertsList({
  status = 'pending',
  ticker,
  enabled = true,
}: {
  status?: KillAlertStatus | 'all';
  ticker?: string | null;
  enabled?: boolean;
}) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId
      ? userKeys.alerts(userId, status, ticker)
      : ['private', 'anonymous', 'kill-alerts', status, ticker?.toUpperCase() ?? 'all'],
    queryFn: () => fetchKillAlerts({ status, ticker }),
    enabled: enabled && !!userId,
    retry: false,
  });
}

export function useKillAlertDetail(alertId: string | null, enabled: boolean = true) {
  const { user } = useAuth();
  const userId = user?.id;

  return useQuery({
    queryKey: userId
      ? userKeys.alert(userId, alertId)
      : ['private', 'anonymous', 'kill-alert', alertId],
    queryFn: () => fetchKillAlert(alertId!),
    enabled: enabled && !!alertId && !!userId,
    retry: false,
  });
}

export function useUpdateKillAlert() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: updateKillAlert,
    onSuccess: (_, variables) => {
      if (!userId) return;
      queryClient.invalidateQueries({ queryKey: ['private', userId, 'kill-alerts'] });
      queryClient.invalidateQueries({ queryKey: userKeys.alert(userId, variables.alertId) });
    },
  });
}

export function useDeleteKillAlert() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const userId = user?.id;

  return useMutation({
    mutationFn: deleteKillAlert,
    onSuccess: (_, alertId) => {
      if (!userId) return;
      queryClient.invalidateQueries({ queryKey: ['private', userId, 'kill-alerts'] });
      queryClient.removeQueries({ queryKey: userKeys.alert(userId, alertId) });
    },
  });
}
