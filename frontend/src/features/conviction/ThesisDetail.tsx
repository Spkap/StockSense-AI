import { useEffect, useState } from 'react';
import { CalendarClock, Edit3, Link2 } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import ThesisEditor from '../../components/ThesisEditor';
import { useThesisComparison, useThesisHistory } from '../../api/theses';
import { cn } from '../../utils/cn';
import type { Thesis } from '../../types/thesis';
import type { FalsifiabilityCompileResult } from '../../types/worldModel';
import BeliefLedgerPanel from './BeliefLedgerPanel';
import ClaimGraphPanel from './ClaimGraphPanel';
import ScenarioBoard from './ScenarioBoard';
import ThesisRunPanel from './ThesisRunPanel';

interface ThesisDetailProps {
  thesis: Thesis | null;
  onCreateFromResearch: (ticker?: string) => void;
}

const convictionStyles: Record<Thesis['conviction_level'], string> = {
  high: 'border-success/25 bg-success/10 text-success',
  medium: 'border-warning/25 bg-warning/10 text-warning',
  low: 'border-border bg-secondary text-muted-foreground',
};

export default function ThesisDetail({ thesis, onCreateFromResearch }: ThesisDetailProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [worldModel, setWorldModel] = useState<FalsifiabilityCompileResult | null>(null);
  const { data: historyData, isLoading: historyLoading } = useThesisHistory(thesis?.id ?? null, Boolean(thesis));
  const { data: comparisonData } = useThesisComparison(thesis?.id ?? null, Boolean(thesis));

  useEffect(() => {
    setIsEditing(false);
    setWorldModel(null);
  }, [thesis?.id]);

  if (!thesis) {
    return (
      <section className="rounded-lg border border-dashed border-border bg-card p-6">
        <div className="grid max-w-xl gap-3">
          <h2 className="text-lg font-semibold">No thesis selected</h2>
          <p className="text-sm text-muted-foreground">
            Create thesis memory from research, then run conviction checks against fresh evidence.
          </p>
          <Button type="button" className="w-fit" onClick={() => onCreateFromResearch()}>
            Create thesis from research
          </Button>
        </div>
      </section>
    );
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-lux dark:shadow-lux-dark">
        <div className="flex flex-col gap-3 border-b border-border px-4 py-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="grid gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-sm font-semibold">{thesis.ticker}</span>
              <Badge variant="outline" className={cn('capitalize', convictionStyles[thesis.conviction_level])}>
                {thesis.conviction_level} conviction
              </Badge>
              <Badge variant="outline" className="capitalize">
                {thesis.status}
              </Badge>
            </div>
            <h2 className="text-xl font-semibold tracking-tight">{thesis.thesis_summary}</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="outline" onClick={() => setIsEditing(true)}>
              <Edit3 />
              Edit Thesis
            </Button>
          </div>
        </div>

        <div className="grid gap-4 p-4">
          <div className="grid gap-2">
            <h3 className="text-sm font-semibold">Kill criteria</h3>
            {thesis.kill_criteria.length > 0 ? (
              <ul className="grid gap-2">
                {thesis.kill_criteria.map((criterion, index) => (
                  <li key={`${criterion}-${index}`} className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3 text-sm">
                    {criterion}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No kill criteria saved.</p>
            )}
          </div>

          <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1">
              <CalendarClock className="size-3" />
              {thesis.time_horizon} horizon
            </span>
            <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1">
              {thesis.thesis_type.replace('_', ' ')}
            </span>
            {thesis.origin_analysis_id ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1">
                <Link2 className="size-3" />
                analysis {thesis.origin_analysis_id}
              </span>
            ) : null}
          </div>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-sm p-5">
          <h3 className="text-sm font-semibold">History</h3>
          {historyLoading ? (
            <p className="mt-2 text-sm text-muted-foreground">Loading thesis history</p>
          ) : (historyData?.history ?? []).length > 0 ? (
            <ol className="mt-3 grid gap-2">
              {(historyData?.history ?? []).slice(0, 5).map((entry) => (
                <li key={entry.id} className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-medium capitalize">{entry.change_type.replace('_', ' ')}</span>
                    <span className="font-mono text-xs text-muted-foreground">{new Date(entry.created_at).toLocaleString()}</span>
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{entry.thesis_summary}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">No history returned.</p>
          )}
        </div>

        <div className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-sm p-5">
          <h3 className="text-sm font-semibold">Comparison</h3>
          {comparisonData?.has_comparison ? (
            <div className="mt-3 grid gap-3">
              <p className="text-sm text-muted-foreground">{comparisonData.change_summary ?? 'Comparison available.'}</p>
              {(comparisonData.changes ?? []).slice(0, 4).map((change) => (
                <div key={`${change.field}-${change.direction}`} className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3 text-sm">
                  <div className="font-medium">{change.field}</div>
                  <div className="text-muted-foreground">
                    {String(change.from)} to {String(change.to)}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-sm text-muted-foreground">
              {comparisonData?.message ?? 'No linked current analysis comparison yet.'}
            </p>
          )}
        </div>
      </section>

      <ThesisRunPanel key={`run-${thesis.id}`} thesisId={thesis.id} ticker={thesis.ticker} />

      <ClaimGraphPanel key={`claims-${thesis.id}`} thesisId={thesis.id} onCompiled={setWorldModel} />
      <ScenarioBoard key={`scenarios-${thesis.id}`} thesisId={thesis.id} />
      <BeliefLedgerPanel
        worldModel={worldModel}
        onForecastResolved={(forecastId, outcome, brierScore) => {
          setWorldModel((current) => {
            if (!current) {
              return current;
            }
            return {
              ...current,
              forecast_questions: current.forecast_questions.map((forecast) =>
                forecast.id === forecastId
                  ? {
                      ...forecast,
                      status: 'resolved',
                      resolved_outcome: outcome,
                      brier_score: brierScore,
                    }
                  : forecast
              ),
            };
          });
        }}
      />

      <ThesisEditor isOpen={isEditing} onClose={() => setIsEditing(false)} ticker={thesis.ticker} existingThesis={thesis} />
    </div>
  );
}
