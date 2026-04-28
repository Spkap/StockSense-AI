import { createAuthenticatedClient } from './authenticated';
import type { FalsifiabilityCompileResult, ScenarioBoardResult } from '../types/worldModel';

export async function compileThesisWorldModel(thesisId: string): Promise<FalsifiabilityCompileResult> {
  const client = await createAuthenticatedClient();
  const { data } = await client.post<FalsifiabilityCompileResult>(`/api/theses/${thesisId}/compile`);
  return data;
}

export async function runWorldModelScenarios(thesisId: string): Promise<ScenarioBoardResult> {
  const client = await createAuthenticatedClient();
  const { data } = await client.post<ScenarioBoardResult>(`/api/theses/${thesisId}/scenarios`);
  return data;
}

export async function resolveForecastQuestion(forecastId: string, outcome: boolean, probability?: number) {
  const client = await createAuthenticatedClient();
  const { data } = await client.post<{ forecast_id: string; status: 'resolved'; brier_score: number }>(
    `/api/forecast-questions/${forecastId}/resolve`,
    { outcome, probability }
  );
  return data;
}
