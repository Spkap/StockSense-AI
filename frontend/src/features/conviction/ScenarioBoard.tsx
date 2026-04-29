import { useState } from 'react';
import { Loader2, Split } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { runWorldModelScenarios } from '../../api/worldModel';
import type { ScenarioBoardResult } from '../../types/worldModel';

export default function ScenarioBoard({ thesisId }: { thesisId: string }) {
  const [result, setResult] = useState<ScenarioBoardResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRun() {
    setError(null);
    setIsLoading(true);
    try {
      setResult(await runWorldModelScenarios(thesisId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scenario run failed.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-border/60 bg-card/75 p-5 shadow-sm backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Scenario board</h3>
          <p className="text-sm text-muted-foreground">Bull, base, and bear paths constrained to claim evidence.</p>
        </div>
        <Button type="button" variant="outline" disabled={isLoading} onClick={() => void handleRun()}>
          {isLoading ? <Loader2 className="animate-spin" /> : <Split />}
          Run scenarios
        </Button>
      </div>
      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}
      {result ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-3">
          {result.scenarios.map(path => (
            <div key={path.scenario} className="rounded-lg border border-border/70 bg-background px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{path.scenario}</Badge>
                <Badge variant="outline">{path.confidence}</Badge>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">{path.summary}</p>
              <div className="mt-3 grid gap-2 text-sm">
                {path.driver_changes.map(driver => <div key={driver}>- {driver}</div>)}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">No scenario run yet.</p>
      )}
    </section>
  );
}
