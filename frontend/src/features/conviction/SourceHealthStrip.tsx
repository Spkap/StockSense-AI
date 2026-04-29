import { AlertCircle, CheckCircle2, CircleDashed, Clock, MinusCircle } from 'lucide-react';
import { cn } from '../../utils/cn';
import type { SourceStatus, SourceType } from '../../types/thesisCheck';

interface SourceHealthStripProps {
  statuses: SourceStatus[];
}

const sourceOrder: SourceType[] = ['news', 'price', 'fundamentals', 'cached_analysis', 'prior_run', 'alert_history'];

const sourceLabels: Record<SourceType, string> = {
  news: 'News',
  price: 'Price',
  fundamentals: 'Fundamentals',
  cached_analysis: 'Cached analysis',
  prior_run: 'Prior run',
  alert_history: 'Alert history',
};

function statusStyles(status?: SourceStatus['status']) {
  switch (status) {
    case 'ok':
      return { icon: CheckCircle2, className: 'border-success/25 bg-success/10 text-success' };
    case 'failed':
    case 'timeout':
      return { icon: AlertCircle, className: 'border-destructive/25 bg-destructive/10 text-destructive' };
    case 'empty':
    case 'skipped':
      return { icon: MinusCircle, className: 'border-warning/25 bg-warning/10 text-warning' };
    default:
      return { icon: CircleDashed, className: 'border-border bg-secondary text-muted-foreground' };
  }
}

export default function SourceHealthStrip({ statuses }: SourceHealthStripProps) {
  const bySource = new Map(statuses.map((status) => [status.source_type, status]));

  return (
    <section className="rounded-lg border border-border/60 bg-card/75 p-4 shadow-sm backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">Source health</h3>
        {statuses.some((status) => ['failed', 'timeout', 'empty', 'skipped'].includes(status.status)) ? (
          <span className="text-xs text-warning">Partial source failure</span>
        ) : null}
      </div>
      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        {sourceOrder.map((source) => {
          const status = bySource.get(source);
          const styles = statusStyles(status?.status);
          const Icon = styles.icon;
          return (
            <div
              key={source}
              className={cn('grid gap-1 rounded-md border px-3 py-2 text-sm', styles.className)}
              title={status?.error ?? undefined}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2 font-medium">
                  <Icon className="size-4" />
                  {sourceLabels[source]}
                </span>
                <span className="capitalize">{status?.status ?? 'pending'}</span>
              </div>
              <span className="flex items-center gap-1 font-mono text-xs opacity-80">
                <Clock className="size-3" />
                {typeof status?.latency_ms === 'number' ? `${status.latency_ms}ms` : 'not run'}
              </span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
