import { useEffect, useMemo, useState } from 'react';
import { AlertCircle, CircleStop, Loader2, Play, RefreshCw } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Progress } from '../../components/ui/progress';
import { useThesisCheckStream } from '../../hooks/useThesisCheckStream';
import { cn } from '../../utils/cn';
import type { ClaimAssessment, ThesisCheckFinal } from '../../types/thesisCheck';
import EvidenceReceipts from './EvidenceReceipts';
import RunInspector from './RunInspector';
import SourceHealthStrip from './SourceHealthStrip';

interface ThesisRunPanelProps {
  thesisId: string;
  ticker: string;
}

const verdictStyles: Record<string, string> = {
  hold: 'border-success/25 bg-success/10 text-success',
  revise: 'border-warning/25 bg-warning/10 text-warning',
  monitor: 'border-warning/25 bg-warning/10 text-warning',
  invalidate: 'border-destructive/25 bg-destructive/10 text-destructive',
  insufficient_evidence: 'border-border bg-secondary text-muted-foreground',
};

function getFinal(finalData: ThesisCheckFinal | null, bundleFinal: ThesisCheckFinal | null): ThesisCheckFinal | null {
  return finalData ?? bundleFinal;
}

function runStatusLabel(status?: string | null): string {
  if (!status) return 'No run';
  return status.replace(/_/g, ' ');
}

function claimList(title: string, items: string[], empty: string) {
  return (
    <div className="grid gap-2 rounded-lg border border-border/80 bg-secondary/35 p-3">
      <h4 className="text-xs font-semibold uppercase text-muted-foreground">{title}</h4>
      {items.length > 0 ? (
        <ul className="grid gap-1 text-sm">
          {items.map((item, index) => (
            <li key={`${item}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground">{empty}</p>
      )}
    </div>
  );
}

export default function ThesisRunPanel({ thesisId, ticker }: ThesisRunPanelProps) {
  const {
    activeRunId,
    events,
    error,
    finalData,
    isStreaming,
    loadLatest,
    phase,
    progress,
    recordCorrection,
    runBundle,
    start,
    stop,
  } = useThesisCheckStream();
  const [hasLoadedLatest, setHasLoadedLatest] = useState(false);

  useEffect(() => {
    setHasLoadedLatest(false);
    loadLatest(thesisId).finally(() => setHasLoadedLatest(true));
  }, [loadLatest, thesisId]);

  const finalResult = getFinal(finalData, runBundle?.run?.final_result ?? null);
  const claimAssessments: ClaimAssessment[] = useMemo(() => {
    return finalResult?.conviction.claim_assessments?.length
      ? finalResult.conviction.claim_assessments
      : finalResult?.evaluation.claim_assessments ?? [];
  }, [finalResult]);

  const runStatus = isStreaming ? 'streaming' : error ? 'error' : runBundle?.run?.status ?? (finalResult ? 'completed' : null);
  const hasPartialSourceFailure = Boolean(
    finalResult?.source_statuses.some((status) => ['failed', 'timeout', 'empty', 'skipped'].includes(status.status))
  );
  const runId = activeRunId ?? finalResult?.run_id ?? runBundle?.run?.id ?? null;

  return (
    <section className="grid gap-4">
      <div className="rounded-lg border border-border/60 bg-card/75 shadow-sm backdrop-blur-md">
        <div className="flex flex-col gap-3 border-b border-border px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-sm font-semibold">Thesis check</h3>
            <p className="break-all text-sm text-muted-foreground">
              {runId ? <span className="font-mono">{runId}</span> : `No saved run for ${ticker}.`}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant="outline"
              className={cn(
                'capitalize',
                runStatus === 'completed' && 'border-success/25 bg-success/10 text-success',
                runStatus === 'streaming' && 'border-primary/25 bg-primary/10 text-primary',
                runStatus === 'cancelled' && 'border-warning/25 bg-warning/10 text-warning',
                runStatus === 'error' && 'border-destructive/25 bg-destructive/10 text-destructive',
                !runStatus && 'border-border bg-secondary text-muted-foreground'
              )}
            >
              {runStatusLabel(runStatus)}
            </Badge>
            {hasPartialSourceFailure ? (
              <Badge variant="outline" className="border-warning/25 bg-warning/10 text-warning">
                Partial source failure
              </Badge>
            ) : null}
          </div>
        </div>

        <div className="grid gap-4 p-4">
          {!hasLoadedLatest && !isStreaming ? (
            <div className="flex items-center gap-2 rounded-md border border-border bg-secondary/35 px-3 py-2 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" />
              Loading latest run
            </div>
          ) : null}

          {isStreaming ? (
            <div className="grid gap-3">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">{phase ?? 'checking thesis'}</span>
                <span className="font-mono text-xs text-muted-foreground">{Math.round(progress * 100)}%</span>
              </div>
              <Progress value={Math.round(progress * 100)} />
              <div className="grid gap-2">
                {events.slice(-5).map((event, index) => (
                  <div
                    key={`${event.run_id}-${event.type}-${index}`}
                    className="flex items-start gap-2 rounded-md border border-border/80 bg-secondary/35 px-3 py-2 text-sm"
                  >
                    <RefreshCw className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" />
                    <div>
                      <div className="font-medium">{event.message}</div>
                      <div className="font-mono text-xs text-muted-foreground">{event.phase}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {error ? (
            <div className="flex items-start gap-2 rounded-md border border-destructive/25 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              {error}
            </div>
          ) : null}

          <div className="grid gap-2 sm:flex sm:flex-wrap">
            <Button type="button" className="w-full sm:w-auto" onClick={() => start(thesisId)} disabled={isStreaming}>
              {isStreaming ? <Loader2 className="animate-spin" /> : <Play />}
              Check thesis now
            </Button>
            {isStreaming ? (
              <Button type="button" variant="outline" className="w-full sm:w-auto" onClick={() => stop()}>
                <CircleStop />
                Cancel
              </Button>
            ) : (
              <Button type="button" variant="outline" className="w-full sm:w-auto" onClick={() => loadLatest(thesisId)}>
                <RefreshCw />
                Reload latest run
              </Button>
            )}
          </div>
        </div>
      </div>

      {finalResult ? (
        <div className="grid gap-4">
          <section className="rounded-lg border border-border/60 bg-card/75 p-4 shadow-sm backdrop-blur-md">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="grid gap-2">
                <Badge
                  variant="outline"
                  className={cn('w-fit capitalize', verdictStyles[finalResult.conviction.verdict] ?? verdictStyles.insufficient_evidence)}
                >
                  Verdict: {finalResult.conviction.verdict.replace(/_/g, ' ')}
                </Badge>
                <h3 className="text-lg font-semibold">{finalResult.conviction.summary}</h3>
              </div>
              <Badge variant="outline" className="w-fit capitalize">
                {finalResult.conviction.confidence} confidence
              </Badge>
            </div>
          </section>

          <section className="grid gap-3 lg:grid-cols-2">
            {claimList('Strengthened', finalResult.conviction.strengthened_claims, 'No thesis claims strengthened.')}
            {claimList('Weakened', finalResult.conviction.weakened_claims, 'No thesis claims weakened.')}
            {claimList('Broke', finalResult.conviction.broken_claims, 'No broken claims found.')}
            {claimList('Unsupported', finalResult.conviction.unsupported_claims, 'No unsupported claims found.')}
          </section>

          <section className="rounded-lg border border-border/60 bg-card/75 p-4 shadow-sm backdrop-blur-md">
            <h3 className="text-sm font-semibold">Contradictions</h3>
            {finalResult.evaluation.contradictions.length > 0 ? (
              <ul className="mt-3 grid gap-2 text-sm">
                {finalResult.evaluation.contradictions.map((item, index) => (
                  <li key={`${item}-${index}`} className="rounded-md border border-destructive/20 bg-destructive/10 px-3 py-2">
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">No contradictions returned.</p>
            )}
          </section>

          <EvidenceReceipts
            claims={claimAssessments}
            evidence={runBundle?.evidence ?? []}
            runId={runId}
            onCorrect={(id, correction) => void recordCorrection(id, correction)}
          />

          <SourceHealthStrip statuses={finalResult.source_statuses} />

          <section className="rounded-lg border border-border/60 bg-card/75 p-4 shadow-sm backdrop-blur-md">
            <h3 className="text-sm font-semibold">Next actions</h3>
            {finalResult.conviction.next_actions.length > 0 ? (
              <ul className="mt-3 grid gap-2 text-sm">
                {finalResult.conviction.next_actions.map((item, index) => (
                  <li key={`${item}-${index}`} className="rounded-md border border-border/80 bg-secondary/35 px-3 py-2">
                    {item}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">No next actions returned.</p>
            )}
          </section>

          <RunInspector bundle={runBundle} />
        </div>
      ) : !isStreaming && hasLoadedLatest ? (
        <div className="rounded-lg border border-dashed border-border bg-card/75 p-5 text-sm text-muted-foreground shadow-sm backdrop-blur-md">
          No check has tested this thesis yet.
        </div>
      ) : null}
    </section>
  );
}
