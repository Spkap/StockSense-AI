import { createAuthenticatedClient } from './authenticated';
import type { ResearchRoomRunBundle, ResearchThesisDraft } from '../types/researchRoom';

export async function getResearchRoomRun(runId: string): Promise<ResearchRoomRunBundle> {
  const client = await createAuthenticatedClient();
  const { data } = await client.get<ResearchRoomRunBundle>(`/api/research-room-runs/${runId}`);
  return data;
}

export async function cancelResearchRoomRun(runId: string): Promise<{ run_id: string; status: 'cancelled' }> {
  const client = await createAuthenticatedClient();
  const { data } = await client.post<{ run_id: string; status: 'cancelled' }>(`/api/research-room-runs/${runId}/cancel`);
  return data;
}

export async function getResearchRoomThesisDraft(runId: string): Promise<ResearchThesisDraft> {
  const client = await createAuthenticatedClient();
  const { data } = await client.post<{ run_id: string; thesis_draft: ResearchThesisDraft }>(
    `/api/research-room-runs/${runId}/thesis-draft`
  );
  return data.thesis_draft;
}
