import { useState } from 'react';
import { GitBranch, Loader2 } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { compileThesisWorldModel } from '../../api/worldModel';
import type { FalsifiabilityCompileResult } from '../../types/worldModel';

interface ClaimGraphPanelProps {
  thesisId: string;
  onCompiled?: (result: FalsifiabilityCompileResult) => void;
}

export default function ClaimGraphPanel({ thesisId, onCompiled }: ClaimGraphPanelProps) {
  const [result, setResult] = useState<FalsifiabilityCompileResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCompile() {
    setError(null);
    setIsLoading(true);
    try {
      const compiled = await compileThesisWorldModel(thesisId);
      setResult(compiled);
      onCompiled?.(compiled);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Compile failed.');
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="rounded-lg border border-border/60 bg-card/75 p-5 shadow-sm backdrop-blur-md">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold">Claim graph</h3>
          <p className="text-sm text-muted-foreground">Compile thesis text into claims, observables, evidence gaps, and forecasts.</p>
        </div>
        <Button type="button" variant="outline" disabled={isLoading} onClick={() => void handleCompile()}>
          {isLoading ? <Loader2 className="animate-spin" /> : <GitBranch />}
          Compile thesis
        </Button>
      </div>

      {error ? <p className="mt-3 text-sm text-destructive">{error}</p> : null}

      {result ? (
        <div className="mt-4 grid gap-3">
          {result.claims.map((claim, index) => (
            <div key={`${claim.claim_text}-${index}`} className="rounded-lg border border-border/70 bg-background px-4 py-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>{claim.claim_type}</Badge>
                <Badge variant="outline">{claim.confidence}</Badge>
                <Badge variant="secondary">{claim.status}</Badge>
              </div>
              <p className="mt-2 text-sm font-medium">{claim.claim_text}</p>
              {claim.observables.length ? (
                <div className="mt-3 grid gap-2">
                  {claim.observables.map(observable => (
                    <div key={`${claim.claim_text}-${observable.observable_name}`} className="rounded-md border border-border/60 bg-secondary/30 px-3 py-2">
                      <div className="text-sm font-medium">{observable.observable_name}</div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {observable.source_type}{observable.metric_key ? ` / ${observable.metric_key}` : ''}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
              {claim.evidence_needed.length ? (
                <div className="mt-3 text-sm text-muted-foreground">
                  Evidence needed: {claim.evidence_needed.join('; ')}
                </div>
              ) : null}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted-foreground">No claim graph compiled yet.</p>
      )}
    </section>
  );
}
