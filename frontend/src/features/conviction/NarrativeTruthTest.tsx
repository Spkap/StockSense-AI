import { Badge } from '../../components/ui/badge';
import type { ClaimAssessment, NarrativeTruthTest as NarrativeTruthTestType } from '../../types/researchRoom';

function stanceLabel(stance: ClaimAssessment['stance']) {
  if (stance === 'supports') return 'Supported';
  if (stance === 'weakens') return 'Weakened';
  if (stance === 'contradicts') return 'Contradicted';
  return 'Missing proof';
}

function ClaimList({ title, claims }: { title: string; claims: ClaimAssessment[] }) {
  if (claims.length === 0) return null;
  return (
    <div className="grid gap-2">
      <h4 className="text-xs font-semibold uppercase text-muted-foreground">{title}</h4>
      <div className="grid gap-2">
        {claims.map((claim, index) => (
          <div key={`${claim.claim}-${index}`} className="rounded-lg border border-border/60 bg-background px-3 py-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="outline">{stanceLabel(claim.stance)}</Badge>
              <Badge variant="secondary">{claim.confidence}</Badge>
              {claim.evidence_refs.map(ref => (
                <span key={ref} className="font-mono text-[11px] text-muted-foreground">{ref}</span>
              ))}
            </div>
            <p className="mt-2 text-sm font-medium">{claim.claim}</p>
            <p className="mt-1 text-sm text-muted-foreground">{claim.rationale}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function NarrativeTruthTest({ test }: { test: NarrativeTruthTestType }) {
  return (
    <div className="grid gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge>{test.verdict}</Badge>
        <Badge variant="outline">{test.confidence} confidence</Badge>
      </div>
      <p className="text-sm leading-6 text-muted-foreground">{test.answer}</p>
      <ClaimList title="Supported" claims={test.supported} />
      <ClaimList title="Weakened" claims={test.weakened} />
      <ClaimList title="Contradicted" claims={test.contradicted} />
      {test.missing_proof.length > 0 ? (
        <div className="grid gap-2">
          <h4 className="text-xs font-semibold uppercase text-muted-foreground">Missing proof</h4>
          <ul className="grid gap-1 text-sm text-muted-foreground">
            {test.missing_proof.map(item => <li key={item}>- {item}</li>)}
          </ul>
        </div>
      ) : null}
      {test.next_watch_items.length > 0 ? (
        <div className="grid gap-2">
          <h4 className="text-xs font-semibold uppercase text-muted-foreground">Next watch items</h4>
          <ul className="grid gap-1 text-sm text-muted-foreground">
            {test.next_watch_items.map(item => <li key={item}>- {item}</li>)}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
