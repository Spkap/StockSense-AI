import { FileText, FlaskConical, Gauge, ListChecks, ReceiptText, SearchCheck } from 'lucide-react';
import type { ReactNode } from 'react';
import { Badge } from '../../components/ui/badge';
import type { ResearchEvidenceItem, ResearchRoomFinal, RunStreamEvent, SourceStatus } from '../../types/researchRoom';
import NarrativeTruthTest from './NarrativeTruthTest';

interface ResearchRoomLanesProps {
  events: RunStreamEvent[];
  finalData: ResearchRoomFinal | null;
  onEvidenceSelect: (evidence: ResearchEvidenceItem) => void;
}

function Lane({ title, icon: Icon, children }: { title: string; icon: typeof FileText; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-border/60 bg-card/60 p-4">
      <div className="mb-3 flex items-center gap-2">
        <Icon className="size-4 text-primary" />
        <h3 className="text-sm font-semibold">{title}</h3>
      </div>
      {children}
    </section>
  );
}

export default function ResearchRoomLanes({ events, finalData, onEvidenceSelect }: ResearchRoomLanesProps) {
  const sourceEvent = events.find(event => event.type === 'source_completed');
  const retrievedIds = events.find(event => event.type === 'retrieval_completed')?.data?.retrieved_ids as string[] | undefined;
  const streamedSourceStatuses = Array.isArray(sourceEvent?.data?.source_statuses)
    ? sourceEvent.data.source_statuses as SourceStatus[]
    : [];
  const sourceStatuses = finalData?.source_statuses.length ? finalData.source_statuses : streamedSourceStatuses;
  const evidenceCount = typeof sourceEvent?.data?.evidence_count === 'number' ? sourceEvent.data.evidence_count : null;

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      <Lane title="Plan" icon={ListChecks}>
        <div className="grid gap-2">
          {events.filter(event => event.type === 'plan_completed' || event.type === 'started').map((event) => (
            <div key={`${event.type}-${event.progress}`} className="rounded-md border border-border/70 bg-background px-3 py-2">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="text-sm font-medium">{event.message}</span>
                <span className="font-mono text-xs text-muted-foreground">{Math.round(event.progress * 100)}%</span>
              </div>
            </div>
          ))}
          {events.length === 0 ? <p className="text-sm text-muted-foreground">No run started.</p> : null}
        </div>
      </Lane>

      <Lane title="Sources" icon={SearchCheck}>
        {sourceStatuses.length ? (
          <div className="grid gap-2">
            {sourceStatuses.map(status => (
              <div key={status.source_type} className="flex items-center justify-between gap-3 rounded-md border border-border/70 bg-background px-3 py-2">
                <span className="text-sm font-medium">{status.source_type}</span>
                <div className="flex items-center gap-2">
                  <Badge variant={status.status === 'ok' ? 'default' : status.status === 'failed' || status.status === 'timeout' ? 'destructive' : 'outline'}>
                    {status.status}
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">{status.latency_ms}ms</span>
                </div>
              </div>
            ))}
            {evidenceCount !== null ? (
              <div className="text-xs text-muted-foreground">{evidenceCount} evidence receipts collected</div>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            {sourceEvent ? 'Source collection finished without status details.' : 'Waiting for source collection.'}
          </p>
        )}
      </Lane>

      <Lane title="Filing Receipts" icon={ReceiptText}>
        {finalData?.evidence.length ? (
          <div className="grid gap-2">
            {finalData.evidence.slice(0, 10).map(item => (
              <button
                key={item.local_id}
                type="button"
                onClick={() => onEvidenceSelect(item)}
                className="rounded-md border border-border/70 bg-background px-3 py-2 text-left transition-colors hover:bg-secondary/50"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs text-primary">{item.local_id}</span>
                  <Badge variant="outline">{item.source_type}</Badge>
                  <Badge variant="secondary">{item.reliability_tier}</Badge>
                </div>
                <p className="mt-1 text-sm font-medium">{item.title}</p>
              </button>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Receipts will appear after collection.</p>
        )}
      </Lane>

      <Lane title="Key Metrics" icon={Gauge}>
        {finalData?.key_metrics.length ? (
          <div className="grid gap-2">
            {finalData.key_metrics.map(metric => (
              <div key={`${metric.metric}-${metric.period ?? ''}`} className="rounded-md border border-border/70 bg-background px-3 py-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-sm font-medium">{metric.metric}</span>
                  <span className="font-mono text-sm">{String(metric.value)}</span>
                </div>
                <div className="mt-1 flex flex-wrap gap-2">
                  {metric.period ? <Badge variant="outline">{metric.period}</Badge> : null}
                  {metric.evidence_refs.map(ref => <span key={ref} className="font-mono text-[11px] text-muted-foreground">{ref}</span>)}
                </div>
                {metric.interpretation ? <p className="mt-2 text-sm text-muted-foreground">{metric.interpretation}</p> : null}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Metrics will appear after analyst review.</p>
        )}
      </Lane>

      <Lane title="Narrative Truth Test" icon={FlaskConical}>
        {finalData ? <NarrativeTruthTest test={finalData.narrative_test} /> : <p className="text-sm text-muted-foreground">Waiting for analyst agents.</p>}
      </Lane>

      <Lane title="Contradictions" icon={FileText}>
        {finalData?.contradiction_cards.length ? (
          <div className="grid gap-2">
            {finalData.contradiction_cards.map(card => (
              <div key={card.title} className="rounded-md border border-border/70 bg-background px-3 py-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={card.severity === 'high' ? 'destructive' : 'outline'}>{card.severity}</Badge>
                  {card.evidence_refs.map(ref => <span key={ref} className="font-mono text-[11px] text-muted-foreground">{ref}</span>)}
                </div>
                <p className="mt-2 text-sm font-medium">{card.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{card.contradiction}</p>
                <p className="mt-1 text-sm text-muted-foreground">{card.why_it_matters}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No contradictions compiled yet.</p>
        )}
      </Lane>

      <Lane title="Memo" icon={FileText}>
        {finalData ? (
          <div className="grid gap-3">
            <p className="text-sm leading-6 text-muted-foreground">{finalData.memo.executive_summary}</p>
            {finalData.memo.missing_proof.length ? (
              <div className="grid gap-1">
                <h4 className="text-xs font-semibold uppercase text-muted-foreground">Missing proof</h4>
                {finalData.memo.missing_proof.map(item => <p key={item} className="text-sm text-muted-foreground">- {item}</p>)}
              </div>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Memo appears at the end of the run.</p>
        )}
      </Lane>

      <Lane title="Thesis Draft" icon={FileText}>
        {finalData ? (
          <div className="grid gap-3">
            <p className="text-sm leading-6">{finalData.thesis_draft.thesis_summary}</p>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{finalData.thesis_draft.conviction_level}</Badge>
              <Badge variant="outline">{finalData.thesis_draft.time_horizon}</Badge>
              <Badge variant="outline">{finalData.thesis_draft.thesis_type}</Badge>
            </div>
            {retrievedIds?.length ? (
              <div className="text-xs text-muted-foreground">Retrieved: {retrievedIds.join(', ')}</div>
            ) : null}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">Draft appears when the memo is complete.</p>
        )}
      </Lane>
    </div>
  );
}
