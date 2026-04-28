import { ChevronDown } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import type { ThesisCheckRunBundle } from '../../types/thesisCheck';

interface RunInspectorProps {
  bundle: ThesisCheckRunBundle | null;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'none';
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  return String(value);
}

export default function RunInspector({ bundle }: RunInspectorProps) {
  const run = bundle?.run ?? null;

  if (!run) {
    return (
      <section className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold">Run inspector</h3>
        <p className="mt-2 text-sm text-muted-foreground">No persisted run metadata is available yet.</p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-border bg-card">
      <details className="group">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3">
          <div>
            <h3 className="text-sm font-semibold">Run inspector</h3>
            <p className="font-mono text-xs text-muted-foreground">{run.id}</p>
          </div>
          <ChevronDown className="size-4 text-muted-foreground transition-transform group-open:rotate-180" />
        </summary>
        <div className="grid gap-4 border-t border-border px-4 py-4">
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ['Run id', run.id],
              ['Evidence hash', run.evidence_hash],
              ['Thesis hash', run.thesis_hash],
              ['Cache hit', run.cache_hit],
              ['Run mode', run.run_mode],
              ['Status', run.status],
              ['Created', new Date(run.created_at).toLocaleString()],
              ['Completed', run.completed_at ? new Date(run.completed_at).toLocaleString() : null],
            ].map(([label, value]) => (
              <div key={String(label)} className="rounded-md border border-border/80 bg-secondary/35 px-3 py-2">
                <div className="text-xs text-muted-foreground">{label}</div>
                <div className="mt-1 break-all font-mono text-xs">{formatValue(value)}</div>
              </div>
            ))}
          </div>

          <div className="overflow-x-auto rounded-md border border-border">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b border-border bg-secondary/50 text-xs uppercase text-muted-foreground">
                <tr>
                  <th className="px-3 py-2 font-medium">Step</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                  <th className="px-3 py-2 font-medium">Latency</th>
                  <th className="px-3 py-2 font-medium">Prompt</th>
                  <th className="px-3 py-2 font-medium">Retries</th>
                  <th className="px-3 py-2 font-medium">Validation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {(bundle?.steps ?? []).map((step) => (
                  <tr key={step.id}>
                    <td className="px-3 py-2 font-medium">{step.step_name}</td>
                    <td className="px-3 py-2">
                      <Badge variant="outline" className="capitalize">
                        {step.status}
                      </Badge>
                    </td>
                    <td className="px-3 py-2 font-mono text-xs">{step.latency_ms}ms</td>
                    <td className="px-3 py-2 font-mono text-xs">{formatValue(step.prompt_version)}</td>
                    <td className="px-3 py-2 font-mono text-xs">{step.retry_count ?? 0}</td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {step.validation_errors && step.validation_errors.length > 0
                        ? step.validation_errors.join(', ')
                        : 'none'}
                    </td>
                  </tr>
                ))}
                {(bundle?.steps ?? []).length === 0 ? (
                  <tr>
                    <td className="px-3 py-4 text-sm text-muted-foreground" colSpan={6}>
                      No step telemetry returned.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </details>
    </section>
  );
}
