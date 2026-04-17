import { useMemo, useState } from 'react';
import { Bell, CheckCheck, Eye, ShieldAlert, Trash2, XCircle } from 'lucide-react';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { useDeleteKillAlert, useKillAlertDetail, useKillAlertsList, useUpdateKillAlert } from '../api/user';
import type { KillAlertStatus } from '../types/api';
import { cn } from '../utils/cn';
import { useAuth } from '../context/AuthContext';

const STATUS_OPTIONS: Array<{ value: KillAlertStatus | 'all'; label: string }> = [
  { value: 'pending', label: 'Pending' },
  { value: 'acknowledged', label: 'Acknowledged' },
  { value: 'dismissed', label: 'Dismissed' },
  { value: 'acted', label: 'Acted' },
  { value: 'all', label: 'All' },
];

export default function AlertsCenter() {
  const { user } = useAuth();
  const [status, setStatus] = useState<KillAlertStatus | 'all'>('pending');
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const { data, isLoading, error } = useKillAlertsList({ status, enabled: !!user });
  const { data: selectedAlert } = useKillAlertDetail(selectedAlertId, !!user);
  const updateAlert = useUpdateKillAlert();
  const deleteAlert = useDeleteKillAlert();

  const alerts = data?.alerts ?? [];
  const unreadAlerts = useMemo(() => alerts.filter((alert) => !alert.is_read), [alerts]);

  const mutateAlertStatus = async (alertId: string, nextStatus: KillAlertStatus, userAction: string) => {
    await updateAlert.mutateAsync({
      alertId,
      update: {
        status: nextStatus,
        user_action: userAction,
      },
    });
  };

  if (!user) {
    return (
      <Card className="border-dashed border-border/60 bg-card/60">
        <CardContent className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <Bell className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold">Sign in to review alerts</h3>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Alert workflows are tied to your theses and positions, so the backend only returns them for authenticated users.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
        <Card className="border-border/50 bg-card shadow-sm">
          <CardHeader className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <CardTitle className="text-2xl">Alerts</CardTitle>
              <CardDescription>Use the backend alert workflow to acknowledge, dismiss, act, or delete thesis alerts.</CardDescription>
            </div>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  variant={status === option.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setStatus(option.value)}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </CardHeader>
          <CardContent className="flex flex-wrap items-center gap-2">
            {unreadAlerts.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={async () => {
                  await Promise.all(
                    unreadAlerts.map((alert) =>
                      mutateAlertStatus(alert.id, 'acknowledged', 'Bulk acknowledged from alerts center')
                    )
                  );
                }}
              >
                <CheckCheck className="h-4 w-4" />
                Acknowledge Visible
              </Button>
            )}
            <span className="text-sm text-muted-foreground">{alerts.length} alerts in this filter</span>
          </CardContent>
        </Card>

        {error && (
          <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
            Failed to load alerts: {error.message}
          </div>
        )}

        {isLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((index) => (
              <div key={index} className="h-28 animate-pulse rounded-xl bg-muted/40" />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <Card className="border-dashed border-border/60 bg-card/60">
            <CardContent className="flex flex-col items-center justify-center py-24 text-center">
              <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Bell className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-semibold">No alerts in this state</h3>
              <p className="mt-2 max-w-md text-sm text-muted-foreground">
                New kill-criteria matches will appear here once your theses and analysis pipeline produce them.
              </p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <Card
                key={alert.id}
                className={cn(
                  'border-border/50 bg-card shadow-sm transition-colors',
                  !alert.is_read && 'border-amber-500/30 bg-amber-500/5'
                )}
              >
                <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-start md:justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600">
                        <ShieldAlert className="h-6 w-6" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-lg font-semibold">{alert.ticker}</h3>
                          <Badge variant="outline" className="capitalize">{alert.data.status}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{new Date(alert.created_at).toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="rounded-xl bg-background/70 p-4">
                      <p className="text-sm font-medium text-foreground">{alert.message || alert.data.triggered_criteria}</p>
                      {alert.data.triggering_signal && (
                        <p className="mt-2 text-sm text-muted-foreground">{alert.data.triggering_signal}</p>
                      )}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2 md:max-w-[260px] md:justify-end">
                    <Button variant="outline" size="sm" className="gap-2" onClick={() => setSelectedAlertId(alert.id)}>
                      <Eye className="h-4 w-4" />
                      Details
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => mutateAlertStatus(alert.id, 'acknowledged', 'Acknowledged from alerts center')}>
                      Acknowledge
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => mutateAlertStatus(alert.id, 'dismissed', 'Dismissed from alerts center')}>
                      <XCircle className="h-4 w-4" />
                      Dismiss
                    </Button>
                    <Button size="sm" onClick={() => mutateAlertStatus(alert.id, 'acted', 'Marked acted from alerts center')}>
                      Mark Acted
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      onClick={() => deleteAlert.mutate(alert.id)}
                      title="Delete alert"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Card className="sticky top-24 h-fit border-border/50 bg-card shadow-sm">
        <CardHeader>
          <CardTitle>Alert Detail</CardTitle>
          <CardDescription>Reads through `GET /api/kill-alerts/{'{id}'}` for the selected alert.</CardDescription>
        </CardHeader>
        <CardContent>
          {!selectedAlert ? (
            <div className="rounded-xl border border-dashed border-border/60 p-8 text-center text-sm text-muted-foreground">
              Select an alert to inspect its backend detail payload.
            </div>
          ) : (
            <div className="space-y-4 text-sm">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Ticker</div>
                <div className="mt-1 font-medium text-foreground">{selectedAlert.ticker}</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Triggered Criteria</div>
                <div className="mt-1 text-foreground">{selectedAlert.data.triggered_criteria}</div>
              </div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Signal</div>
                <div className="mt-1 text-foreground">{selectedAlert.data.triggering_signal}</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-xl bg-secondary/40 p-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Match Confidence</div>
                  <div className="mt-1 text-lg font-semibold text-foreground">{Math.round(selectedAlert.data.match_confidence * 100)}%</div>
                </div>
                <div className="rounded-xl bg-secondary/40 p-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Status</div>
                  <div className="mt-1 text-lg font-semibold capitalize text-foreground">{selectedAlert.data.status}</div>
                </div>
              </div>
              {selectedAlert.data.analysis_summary && (
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Analysis Summary</div>
                  <div className="mt-1 text-muted-foreground">{selectedAlert.data.analysis_summary}</div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
