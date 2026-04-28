import { useEffect, useMemo, useState } from 'react';
import { Bell, CheckCircle2, ExternalLink, Loader2, XCircle } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { useKillAlertDetail, useKillAlertsList, useUpdateKillAlert } from '../../api/user';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../utils/cn';
import type { KillAlert } from '../../types/api';

interface AlertsQueueProps {
  onOpenThesis: (thesisId: string) => void;
}

const statusStyles: Record<string, string> = {
  pending: 'border-warning/25 bg-warning/10 text-warning',
  acknowledged: 'border-success/25 bg-success/10 text-success',
  acted: 'border-primary/25 bg-primary/10 text-primary',
  dismissed: 'border-border bg-secondary text-muted-foreground',
};

function sortAlerts(alerts: KillAlert[]): KillAlert[] {
  return [...alerts].sort((a, b) => {
    const aPending = a.data.status === 'pending' ? 0 : 1;
    const bPending = b.data.status === 'pending' ? 0 : 1;
    if (aPending !== bPending) return aPending - bPending;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
}

export default function AlertsQueue({ onOpenThesis }: AlertsQueueProps) {
  const { user } = useAuth();
  const { data, isLoading, isError } = useKillAlertsList({ status: 'all', enabled: Boolean(user) });
  const alerts = useMemo(() => sortAlerts(data?.alerts ?? []), [data?.alerts]);
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const selectedFallback = alerts.find((alert) => alert.id === selectedAlertId) ?? alerts[0] ?? null;
  const { data: selectedDetail } = useKillAlertDetail(selectedFallback?.id ?? null, Boolean(user && selectedFallback));
  const selectedAlert = selectedDetail ?? selectedFallback;
  const updateAlert = useUpdateKillAlert();

  useEffect(() => {
    if (!selectedAlertId && alerts[0]) {
      setSelectedAlertId(alerts[0].id);
    }
  }, [alerts, selectedAlertId]);

  if (!user) {
    return (
      <section className="rounded-lg border border-border bg-card p-4 md:p-5">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)] lg:items-center">
          <div className="grid gap-3">
            <h2 className="text-lg font-semibold">Sign in to review kill alerts.</h2>
            <p className="text-sm text-muted-foreground">Alerts are generated from your saved thesis criteria.</p>
          </div>
          <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1">
            {[
              ['Pending first', 'Unresolved thesis breaks'],
              ['Evidence', 'Signal and confidence detail'],
              ['Actions', 'Acknowledge, dismiss, open thesis'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-md border border-border/80 bg-secondary/35 px-3 py-2">
                <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
                <div className="mt-1 text-sm">{value}</div>
              </div>
            ))}
          </div>
        </div>
      </section>
    );
  }

  if (isError) {
    return (
      <section className="rounded-lg border border-destructive/25 bg-destructive/10 p-6 text-destructive">
        <h2 className="text-lg font-semibold">Could not load alerts</h2>
        <p className="mt-2 text-sm">The backend rejected the kill-alert request.</p>
      </section>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
      <section className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-sm">
        <div className="border-b border-border px-4 py-3">
          <h2 className="text-sm font-semibold">Alert queue</h2>
          <p className="text-xs text-muted-foreground">Pending alerts are listed first.</p>
        </div>
        <div className="max-h-[calc(100dvh-230px)] overflow-y-auto p-2">
          {isLoading ? (
            <div className="grid gap-2 p-2">
              {[0, 1, 2].map((item) => (
                <div key={item} className="h-24 animate-pulse rounded-md bg-secondary" />
              ))}
            </div>
          ) : alerts.length > 0 ? (
            <div className="grid gap-1">
              {alerts.map((alert) => {
                const selected = alert.id === selectedAlert?.id;
                return (
                  <button
                    key={alert.id}
                    type="button"
                    onClick={() => setSelectedAlertId(alert.id)}
                    className={cn(
                      'grid gap-2 rounded-xl px-4 py-3.5 text-left transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                      selected ? 'bg-primary text-primary-foreground shadow-lux dark:shadow-lux-dark scale-[1.01]' : 'hover:bg-secondary/60 hover:shadow-sm hover:scale-[1.01] border border-transparent hover:border-border/50'
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-sm font-semibold">{alert.ticker}</span>
                          <Badge
                            variant="outline"
                            className={cn(
                              'capitalize',
                              selected ? 'border-primary-foreground/30 text-primary-foreground' : statusStyles[alert.data.status]
                            )}
                          >
                            {alert.data.status}
                          </Badge>
                        </div>
                        <p className={cn('mt-1 line-clamp-2 text-sm', selected ? 'text-primary-foreground/80' : 'text-muted-foreground')}>
                          {alert.message}
                        </p>
                      </div>
                      <Bell className={cn('mt-1 size-4 shrink-0', selected ? 'text-primary-foreground/70' : 'text-muted-foreground')} />
                    </div>
                    <span className={cn('font-mono text-xs', selected ? 'text-primary-foreground/70' : 'text-muted-foreground')}>
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <p className="p-4 text-sm text-muted-foreground">No kill alerts returned.</p>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-lux dark:shadow-lux-dark">
        {selectedAlert ? (
          <div className="grid gap-4 p-4">
            <div className="flex flex-col gap-3 border-b border-border pb-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="grid gap-2">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="font-mono">
                    {selectedAlert.ticker}
                  </Badge>
                  <Badge variant="outline" className={cn('capitalize', statusStyles[selectedAlert.data.status])}>
                    {selectedAlert.data.status}
                  </Badge>
                  <Badge variant="outline">{selectedAlert.alert_type}</Badge>
                </div>
                <h2 className="text-xl font-semibold">{selectedAlert.message}</h2>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={updateAlert.isPending}
                  onClick={() =>
                    updateAlert.mutate({
                      alertId: selectedAlert.id,
                      update: { status: 'acknowledged', user_action: 'Acknowledged from Conviction Desk' },
                    })
                  }
                >
                  {updateAlert.isPending ? <Loader2 className="animate-spin" /> : <CheckCircle2 />}
                  Acknowledge
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={updateAlert.isPending}
                  onClick={() =>
                    updateAlert.mutate({
                      alertId: selectedAlert.id,
                      update: { status: 'dismissed', user_action: 'Dismissed from Conviction Desk' },
                    })
                  }
                >
                  <XCircle />
                  Dismiss
                </Button>
                <Button type="button" onClick={() => onOpenThesis(selectedAlert.thesis_id)}>
                  <ExternalLink />
                  Open linked thesis
                </Button>
              </div>
            </div>

            <div className="grid gap-3 lg:grid-cols-2">
              {[
                ['Triggered criteria', selectedAlert.data.triggered_criteria],
                ['Signal', selectedAlert.data.triggering_signal],
                ['Match confidence', `${Math.round(selectedAlert.data.match_confidence * 100)}%`],
                ['Status', selectedAlert.data.status],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3">
                  <div className="text-xs font-medium uppercase text-muted-foreground">{label}</div>
                  <div className="mt-1 text-sm">{value}</div>
                </div>
              ))}
            </div>

            <div className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3">
              <div className="text-xs font-medium uppercase text-muted-foreground">Analysis summary</div>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {selectedAlert.data.analysis_summary ?? 'No analysis summary stored for this alert.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="p-6 text-sm text-muted-foreground">Select an alert to review details.</div>
        )}
      </section>
    </div>
  );
}
