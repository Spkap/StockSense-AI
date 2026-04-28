import { AlertTriangle, CheckCircle2, HelpCircle, MinusCircle } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { cn } from '../../utils/cn';
import type { ClaimAssessment, EvidenceItem, ThesisCorrectionRequest } from '../../types/thesisCheck';

interface EvidenceReceiptsProps {
  claims: ClaimAssessment[];
  evidence: EvidenceItem[];
  runId?: string | null;
  onCorrect?: (runId: string, correction: ThesisCorrectionRequest) => void;
}

const stanceConfig = {
  supports: { label: 'Supports', className: 'border-success/25 bg-success/10 text-success', icon: CheckCircle2 },
  weakens: { label: 'Weakens', className: 'border-warning/25 bg-warning/10 text-warning', icon: MinusCircle },
  contradicts: {
    label: 'Contradicts',
    className: 'border-destructive/25 bg-destructive/10 text-destructive',
    icon: AlertTriangle,
  },
  unsupported: { label: 'Unsupported', className: 'border-border bg-secondary text-muted-foreground', icon: HelpCircle },
} as const;

function evidenceLabel(item: EvidenceItem): string {
  return item.local_id || item.id || item.evidence_hash || item.title;
}

export default function EvidenceReceipts({ claims, evidence, runId, onCorrect }: EvidenceReceiptsProps) {
  const evidenceByRef = new Map<string, EvidenceItem>();
  evidence.forEach((item) => {
    [item.local_id, item.id, item.evidence_hash].forEach((ref) => {
      if (ref) evidenceByRef.set(ref, item);
    });
  });

  if (claims.length === 0) {
    return (
      <section className="rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-semibold">Evidence receipts</h3>
        <p className="mt-2 text-sm text-muted-foreground">No claim-level evidence was returned for this run.</p>
      </section>
    );
  }

  return (
    <section className="rounded-lg border border-border bg-card">
      <div className="border-b border-border px-4 py-3">
        <h3 className="text-sm font-semibold">Evidence receipts</h3>
      </div>
      <div className="divide-y divide-border">
        {claims.map((claim, index) => {
          const config = stanceConfig[claim.stance];
          const Icon = config.icon;
          const refs = claim.evidence_refs
            .map((ref) => evidenceByRef.get(ref) ?? evidence.find((item) => evidenceLabel(item) === ref))
            .filter((item): item is EvidenceItem => Boolean(item));

          return (
            <article key={`${claim.claim}-${index}`} className="grid gap-3 px-4 py-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="grid gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className={cn('gap-1.5', config.className)}>
                      <Icon className="size-3" />
                      {config.label}
                    </Badge>
                    <Badge variant="outline" className="capitalize">
                      {claim.confidence} confidence
                    </Badge>
                  </div>
                  <p className="text-sm font-medium leading-6">{claim.claim}</p>
                </div>
                {runId && onCorrect ? (
                  <div className="flex shrink-0 flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        onCorrect(runId, {
                          correction_type: 'evidence_irrelevant',
                          correction_text: 'Marked by user as irrelevant to the claim.',
                          claim: claim.claim,
                          evidence_local_id: claim.evidence_refs[0] ?? null,
                        })
                      }
                    >
                      Mark irrelevant
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        onCorrect(runId, {
                          correction_type: 'needs_better_evidence',
                          correction_text: 'User requested stronger evidence for this claim.',
                          claim: claim.claim,
                          evidence_local_id: claim.evidence_refs[0] ?? null,
                        })
                      }
                    >
                      Needs better evidence
                    </Button>
                  </div>
                ) : null}
              </div>

              <p className="text-sm text-muted-foreground">{claim.rationale}</p>

              <div className="grid gap-2">
                {refs.length > 0 ? (
                  refs.map((item, refIndex) => (
                    <div
                      key={`${evidenceLabel(item)}-${refIndex}`}
                      className="grid gap-1 rounded-md border border-border/80 bg-secondary/35 px-3 py-2"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-xs text-muted-foreground">{evidenceLabel(item)}</span>
                        <Badge variant="outline" className="capitalize">
                          {item.source_type.replace('_', ' ')}
                        </Badge>
                        <Badge variant="outline" className="capitalize">
                          {item.reliability_tier} reliability
                        </Badge>
                      </div>
                      <div className="text-sm font-medium">{item.title || item.source_name}</div>
                      <p className="line-clamp-3 text-sm text-muted-foreground">{item.text}</p>
                      {item.url ? (
                        <a
                          href={item.url}
                          target="_blank"
                          rel="noreferrer"
                          className="w-fit text-xs font-medium text-primary hover:underline"
                        >
                          Open source
                        </a>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <div className="rounded-md border border-border/80 bg-secondary/35 px-3 py-2 text-sm text-muted-foreground">
                    Evidence references: {claim.evidence_refs.length > 0 ? claim.evidence_refs.join(', ') : 'none'}
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
