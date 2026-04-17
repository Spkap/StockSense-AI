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

export const userKeys = {
  profile: ['profile'] as const,
  positions: ['positions'] as const,
  alerts: (status: string, ticker?: string | null) => ['kill-alerts', status, ticker?.toUpperCase() ?? 'all'] as const,
  alert: (alertId: string | null) => ['kill-alert', alertId] as const,
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
  return useQuery({
    queryKey: userKeys.profile,
    queryFn: fetchProfile,
    enabled,
    retry: false,
  });
}

export function usePositions(enabled: boolean = true) {
  return useQuery({
    queryKey: userKeys.positions,
    queryFn: fetchPositions,
    enabled,
    retry: false,
  });
}

export function useCreatePosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createPosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.positions });
    },
  });
}

export function useDeletePosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deletePosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.positions });
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
  return useQuery({
    queryKey: userKeys.alerts(status, ticker),
    queryFn: () => fetchKillAlerts({ status, ticker }),
    enabled,
    retry: false,
  });
}

export function useKillAlertDetail(alertId: string | null, enabled: boolean = true) {
  return useQuery({
    queryKey: userKeys.alert(alertId),
    queryFn: () => fetchKillAlert(alertId!),
    enabled: enabled && !!alertId,
    retry: false,
  });
}

export function useUpdateKillAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: updateKillAlert,
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['kill-alerts'] });
      queryClient.invalidateQueries({ queryKey: userKeys.alert(variables.alertId) });
    },
  });
}

export function useDeleteKillAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteKillAlert,
    onSuccess: (_, alertId) => {
      queryClient.invalidateQueries({ queryKey: ['kill-alerts'] });
      queryClient.removeQueries({ queryKey: userKeys.alert(alertId) });
    },
  });
}
