import type { AnalysisData, KillAlert } from '../../types/api';
import type { Thesis } from '../../types/thesis';

export type ConvictionView = 'workbench' | 'research' | 'alerts';

export interface AnalysisSnapshotInput {
  sentiment: string;
  confidence: number;
  skeptic_verdict?: string;
  key_themes?: string[];
  timestamp: string;
}

export function buildAnalysisSnapshot(data: AnalysisData | null): AnalysisSnapshotInput | undefined {
  if (!data) return undefined;

  return {
    sentiment: data.overall_sentiment || data.sentiment_report?.slice(0, 80) || 'Unknown',
    confidence: typeof data.overall_confidence === 'number' ? data.overall_confidence : 0,
    skeptic_verdict: data.skeptic_sentiment || data.primary_disagreement,
    key_themes: data.key_themes?.map((theme) => theme.theme).slice(0, 5),
    timestamp: data.timestamp,
  };
}

export function sortThesesByUpdatedAt(theses: Thesis[]): Thesis[] {
  return [...theses].sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());
}

export function findThesisForAlert(theses: Thesis[], alert: KillAlert | null): Thesis | null {
  if (!alert) return null;
  return theses.find((thesis) => thesis.id === alert.thesis_id) ?? null;
}

