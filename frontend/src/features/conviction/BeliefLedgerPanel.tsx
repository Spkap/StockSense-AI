import { useState } from 'react';
import { CheckCircle2, XCircle } from 'lucide-react';
import { resolveForecastQuestion } from '../../api/worldModel';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { useToast } from '../../components/ui/toast';
import type { FalsifiabilityCompileResult, ForecastQuestion } from '../../types/worldModel';

interface BeliefLedgerPanelProps {
  worldModel: FalsifiabilityCompileResult | null;
  onForecastResolved?: (forecastId: string, outcome: boolean, brierScore: number) => void;
}

export default function BeliefLedgerPanel({ worldModel, onForecastResolved }: BeliefLedgerPanelProps) {
  const [pendingForecastId, setPendingForecastId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { addToast } = useToast();
  const forecasts = worldModel?.forecast_questions ?? [];
  const open = forecasts.filter(forecast => forecast.status === 'open');
  const resolved = forecasts.filter(forecast => forecast.status === 'resolved');

  async function handleResolve(forecast: ForecastQuestion, outcome: boolean) {
    if (!forecast.id || pendingForecastId) {
      return;
    }

    setPendingForecastId(forecast.id);
    setError(null);

    try {
      const result = await resolveForecastQuestion(forecast.id, outcome, forecast.probability ?? undefined);
      onForecastResolved?.(forecast.id, outcome, result.brier_score);
      addToast({
        type: 'success',
        title: 'Forecast resolved',
        message: `Brier score ${result.brier_score.toFixed(2)}`,
      });
    } catch {
      setError('Forecast resolution failed.');
      addToast({
        type: 'error',
        title: 'Forecast resolution failed',
        message: 'The ledger did not update.',
      });
    } finally {
      setPendingForecastId(null);
    }
  }

  return (
    <section className="rounded-2xl border border-border/60 bg-card/60 p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Belief ledger</h3>
          <p className="text-sm text-muted-foreground">Forecast questions and calibration scaffolding from the claim graph.</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline">{open.length} open</Badge>
          <Badge variant="secondary">{resolved.length} resolved</Badge>
        </div>
      </div>

      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}

      {forecasts.length ? (
        <div className="mt-4 grid gap-2">
          {forecasts.slice(0, 5).map((forecast, index) => (
            <div key={forecast.id ?? `${forecast.question}-${index}`} className="rounded-lg border border-border/70 bg-background px-4 py-3">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge>{forecast.status}</Badge>
                  {typeof forecast.probability === 'number' ? <Badge variant="outline">{Math.round(forecast.probability * 100)}%</Badge> : null}
                  {forecast.status === 'resolved' && typeof forecast.resolved_outcome === 'boolean' ? (
                    <Badge variant="secondary">{forecast.resolved_outcome ? 'yes' : 'no'}</Badge>
                  ) : null}
                  {typeof forecast.brier_score === 'number' ? <Badge variant="outline">Brier {forecast.brier_score.toFixed(2)}</Badge> : null}
                </div>
                {forecast.status === 'open' && forecast.id ? (
                  <div className="flex shrink-0 gap-1.5">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-8 px-2.5 text-xs"
                      disabled={pendingForecastId === forecast.id}
                      onClick={() => handleResolve(forecast, true)}
                      aria-label="Resolve forecast as yes"
                    >
                      <CheckCircle2 className="size-3.5" />
                      Yes
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-8 px-2.5 text-xs"
                      disabled={pendingForecastId === forecast.id}
                      onClick={() => handleResolve(forecast, false)}
                      aria-label="Resolve forecast as no"
                    >
                      <XCircle className="size-3.5" />
                      No
                    </Button>
                  </div>
                ) : null}
              </div>
              <p className="mt-2 text-sm font-medium">{forecast.question}</p>
              <p className="mt-1 text-sm text-muted-foreground">{forecast.resolution_criteria}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">Compile a claim graph to create forecast questions.</p>
      )}
    </section>
  );
}
