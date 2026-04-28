import { AlertTriangle, CheckCircle, Circle, Clock, Database, FileText, Loader2, RefreshCw, ShieldAlert, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import type { ClaimAssessment, EvidenceItem, SourceStatus, ThesisCheckFinal, ThesisCheckRunBundle, ThesisCheckStreamEvent, ThesisCorrectionRequest } from '../types/thesisCheck';

interface ThesisCheckPanelProps {
  ticker: string;
  isStreaming: boolean;
  progress: number;
  phase: string | null;
  events: ThesisCheckStreamEvent[];
  finalData: ThesisCheckFinal | null;
  runBundle: ThesisCheckRunBundle | null;
  error: string | null;
  onStart: () => void;
  onStop: () => void;
  onCorrect: (runId: string, correction: ThesisCorrectionRequest) => void;
}

const lanes = [
  { id: 'evidence', label: 'Evidence' },
  { id: 'memory', label: 'Memory' },
  { id: 'challenge', label: 'Challenge' },
  { id: 'conviction', label: 'Conviction' },
];

function laneStatus(lane: string, phase: string | null, finalData: ThesisCheckFinal | null, error: string | null) {
  if (error) return 'failed';
  if (finalData) return 'done';
  if (phase === lane) return 'active';
  const order = ['evidence', 'memory', 'challenge', 'conviction'];
  const currentIndex = phase ? order.indexOf(phase) : -1;
  const laneIndex = order.indexOf(lane);
  if (currentIndex > laneIndex) return 'done';
  return 'pending';
}

function getLatestSourceStatuses(events: ThesisCheckStreamEvent[], finalData: ThesisCheckFinal | null): SourceStatus[] {
  if (finalData?.source_statuses?.length) return finalData.source_statuses;

  const sourceEvent = [...events].reverse().find(event => Array.isArray(event.data?.source_statuses));
  if (!sourceEvent) return [];
  return sourceEvent.data.source_statuses as SourceStatus[];
}

function statusTone(status: SourceStatus['status']) {
  if (status === 'ok') return 'border-success/20 bg-success/5 text-success';
  if (status === 'empty' || status === 'skipped') return 'border-warning/20 bg-warning/5 text-warning';
  if (status === 'failed' || status === 'timeout') return 'border-destructive/20 bg-destructive/5 text-destructive';
  return 'border-border/40 bg-background/60 text-muted-foreground';
}

function evidenceByLocalId(evidence: EvidenceItem[]) {
  return evidence.reduce<Record<string, EvidenceItem>>((acc, item) => {
    const id = item.local_id ?? item.id;
    if (id) acc[id] = item;
    return acc;
  }, {});
}

function getClaimAssessments(finalData: ThesisCheckFinal | null): ClaimAssessment[] {
  if (!finalData) return [];
  const convictionClaims = finalData.conviction.claim_assessments ?? [];
  if (convictionClaims.length > 0) return convictionClaims;
  return finalData.evaluation.claim_assessments ?? [];
}

export default function ThesisCheckPanel({
  ticker,
  isStreaming,
  progress,
  phase,
  events,
  finalData,
  runBundle,
  error,
  onStart,
  onStop,
  onCorrect,
}: ThesisCheckPanelProps) {
  const latestMessage = events.length > 0 ? events[events.length - 1]?.message : undefined;
  const sourceStatuses = getLatestSourceStatuses(events, finalData);
  const run = runBundle?.run ?? null;
  const steps = runBundle?.steps ?? [];
  const evidenceItems = runBundle?.evidence ?? [];
  const evidenceLookup = evidenceByLocalId(evidenceItems);
  const claimAssessments = getClaimAssessments(finalData);
  const latestCompletedAt = run?.completed_at ?? run?.created_at;

  return (
    <div className="rounded-xl border border-border/50 bg-card p-4">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h4 className="text-sm font-semibold text-foreground">{ticker} Thesis Check</h4>
          <p className="text-xs text-muted-foreground">
            Evidence, memory, challenge, and conviction diff.
          </p>
          {run && !isStreaming && (
            <p className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              Latest run {run.status.replace('_', ' ')}
              {latestCompletedAt ? ` on ${new Date(latestCompletedAt).toLocaleString()}` : ''}
            </p>
          )}
        </div>

        <div className="flex items-center gap-2">
          {isStreaming ? (
            <Button variant="outline" size="sm" onClick={onStop}>
              Stop
            </Button>
          ) : (
            <Button size="sm" onClick={onStart} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Check Thesis
            </Button>
          )}
        </div>
      </div>

      {(isStreaming || events.length > 0 || finalData || error) && (
        <div className="mt-4 space-y-4">
          <div>
            <div className="mb-2 flex items-center justify-between text-xs">
              <span className="font-medium text-muted-foreground">{latestMessage ?? phase ?? 'ready'}</span>
              <span className="font-mono text-muted-foreground">{Math.round(progress * 100)}%</span>
            </div>
            <Progress value={progress * 100} className="h-2" />
          </div>

          <div className="grid gap-2 md:grid-cols-4">
            {lanes.map(lane => {
              const status = laneStatus(lane.id, phase, finalData, error);
              return (
                <div key={lane.id} className="rounded-lg border border-border/40 bg-background/50 p-3">
                  <div className="flex items-center gap-2 text-sm font-medium">
                    {status === 'done' && <CheckCircle className="h-4 w-4 text-success" />}
                    {status === 'active' && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                    {status === 'failed' && <AlertTriangle className="h-4 w-4 text-destructive" />}
                    {status === 'pending' && <Circle className="h-4 w-4 text-muted-foreground" />}
                    <span>{lane.label}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {sourceStatuses.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Database className="h-3.5 w-3.5" />
                Source Health
              </div>
              <div className="grid gap-2 md:grid-cols-3">
                {sourceStatuses.map(status => (
                  <div
                    key={status.source_type}
                    className={`rounded-lg border p-3 text-xs ${statusTone(status.status)}`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold capitalize">{status.source_type.replace('_', ' ')}</span>
                      <span className="font-mono">{status.latency_ms}ms</span>
                    </div>
                    <div className="mt-1 capitalize">{status.status}</div>
                    {status.error && <div className="mt-1 text-[11px] opacity-80">{status.error}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {finalData && (
            <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
              <div className="flex items-start gap-3">
                <Sparkles className="mt-0.5 h-5 w-5 text-primary" />
                <div>
                  <div className="text-sm font-semibold capitalize">
                    Verdict: {finalData.conviction.verdict.replace('_', ' ')}
                    {finalData.cache_hit && <span className="ml-2 text-xs font-medium text-success">Cached</span>}
                  </div>
                  <p className="mt-1 text-sm text-muted-foreground">
                    {finalData.conviction.summary}
                  </p>
                </div>
              </div>

              {finalData.evaluation.contradictions.length > 0 && (
                <div>
                  <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-warning">
                    <ShieldAlert className="h-3 w-3" />
                    Contradictions
                  </div>
                  <ul className="space-y-1 text-sm text-foreground/90">
                    {finalData.evaluation.contradictions.map((item, index) => (
                      <li key={index}>- {item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {claimAssessments.length > 0 && (
                <div>
                  <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <FileText className="h-3 w-3" />
                    Claim Receipts
                  </div>
                  <div className="space-y-2">
                    {claimAssessments.slice(0, 5).map((claim, index) => (
                      <div key={`${claim.claim}-${index}`} className="rounded-lg border border-border/50 bg-background/60 p-3">
                        <div className="flex flex-col gap-1 md:flex-row md:items-start md:justify-between">
                          <div className="text-sm font-medium text-foreground">{claim.claim}</div>
                          <span className="w-fit rounded-md border border-border/50 px-2 py-0.5 text-[11px] capitalize text-muted-foreground">
                            {claim.stance} / {claim.confidence}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{claim.rationale}</p>
                        {claim.evidence_refs.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {claim.evidence_refs.map(ref => {
                              const evidence = evidenceLookup[ref];
                              return (
                                <div key={ref} className="rounded-md border border-border/40 bg-card px-2 py-1.5 text-xs">
                                  <span className="font-mono text-muted-foreground">{ref}</span>
                                  {evidence ? (
                                    <span className="ml-2 text-foreground/90">{evidence.title}</span>
                                  ) : (
                                    <span className="ml-2 text-warning">Evidence receipt unavailable in latest run payload</span>
                                  )}
                                </div>
                              );
                            })}
                          </div>
                        )}
                        {run?.id && (
                          <div className="mt-2 flex flex-wrap gap-2">
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => onCorrect(run.id, {
                                correction_type: 'evidence_irrelevant',
                                correction_text: 'User marked this evidence as irrelevant to the claim.',
                                claim: claim.claim,
                                evidence_local_id: claim.evidence_refs[0] ?? null,
                              })}
                            >
                              Mark Irrelevant
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={() => onCorrect(run.id, {
                                correction_type: 'needs_better_evidence',
                                correction_text: 'User wants stronger evidence before trusting this assessment.',
                                claim: claim.claim,
                                evidence_local_id: claim.evidence_refs[0] ?? null,
                              })}
                            >
                              Needs Better Evidence
                            </Button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {finalData.conviction.next_actions.length > 0 && (
                <div>
                  <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Next Actions
                  </div>
                  <ul className="space-y-1 text-sm text-foreground/90">
                    {finalData.conviction.next_actions.map((item, index) => (
                      <li key={index}>- {item}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {steps.length > 0 && (
            <details className="rounded-lg border border-border/50 bg-background/50 p-3">
              <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Run Inspector
              </summary>
              <div className="mt-3 space-y-2">
                {run && (
                  <div className="grid gap-2 text-xs md:grid-cols-3">
                    <div>
                      <div className="font-semibold text-foreground/70">Run</div>
                      <div className="font-mono text-muted-foreground">{run.id}</div>
                    </div>
                    <div>
                      <div className="font-semibold text-foreground/70">Evidence Hash</div>
                      <div className="truncate font-mono text-muted-foreground">{run.evidence_hash ?? 'none'}</div>
                    </div>
                    <div>
                      <div className="font-semibold text-foreground/70">Cache</div>
                      <div className="text-muted-foreground">{run.cache_hit ? 'hit' : 'miss'}</div>
                    </div>
                  </div>
                )}
                <div className="space-y-1">
                  {steps.map(step => (
                    <div key={step.id} className="grid gap-2 rounded-md border border-border/40 bg-card px-2 py-1.5 text-xs md:grid-cols-[1.3fr_0.7fr_0.7fr_1fr]">
                      <span className="font-medium text-foreground">{step.step_name}</span>
                      <span className="capitalize text-muted-foreground">{step.status}</span>
                      <span className="font-mono text-muted-foreground">{step.latency_ms}ms</span>
                      <span className="truncate text-muted-foreground">
                        {step.prompt_version ? `prompt ${step.prompt_version}` : step.retry_count ? `${step.retry_count} retry` : ''}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}
