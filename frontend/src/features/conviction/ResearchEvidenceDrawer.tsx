import { ExternalLink, X } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import type { ResearchEvidenceItem } from '../../types/researchRoom';

interface ResearchEvidenceDrawerProps {
  evidence: ResearchEvidenceItem | null;
  onClose: () => void;
}

export default function ResearchEvidenceDrawer({ evidence, onClose }: ResearchEvidenceDrawerProps) {
  if (!evidence) return null;

  return (
    <div className="fixed inset-0 z-50 bg-background/60 backdrop-blur-sm" role="presentation" onClick={onClose}>
      <aside
        className="absolute right-0 top-0 h-full w-full max-w-xl overflow-y-auto border-l border-border bg-background p-4 shadow-xl sm:p-5"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="grid gap-2">
            <Badge variant="outline" className="w-fit max-w-full break-all font-mono">{evidence.local_id}</Badge>
            <h2 className="text-lg font-semibold">{evidence.title}</h2>
          </div>
          <Button type="button" variant="ghost" size="icon" onClick={onClose} aria-label="Close evidence">
            <X />
          </Button>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Badge>{evidence.source_type}</Badge>
          <Badge variant="secondary">{evidence.reliability_tier}</Badge>
          {evidence.filing_type ? <Badge variant="outline">{evidence.filing_type}</Badge> : null}
          {evidence.period ? <Badge variant="outline">{evidence.period}</Badge> : null}
        </div>

        <dl className="mt-5 grid gap-3 text-sm">
          <div>
            <dt className="text-xs font-semibold uppercase text-muted-foreground">Source</dt>
            <dd className="mt-1">{evidence.source_name}</dd>
          </div>
          {evidence.accession_number ? (
            <div>
              <dt className="text-xs font-semibold uppercase text-muted-foreground">Accession</dt>
              <dd className="mt-1 break-all font-mono text-xs">{evidence.accession_number}</dd>
            </div>
          ) : null}
          {evidence.metric_name ? (
            <div>
              <dt className="text-xs font-semibold uppercase text-muted-foreground">Metric</dt>
              <dd className="mt-1">{evidence.metric_name}: {String(evidence.metric_value ?? '')}</dd>
            </div>
          ) : null}
        </dl>

        <div className="mt-5 rounded-lg border border-border/70 bg-secondary/30 p-4">
          <p className="whitespace-pre-wrap text-sm leading-6">{evidence.text}</p>
        </div>

        {evidence.url ? (
          <a
            href={evidence.url}
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
          >
            <ExternalLink className="size-4" />
            Open source
          </a>
        ) : null}
      </aside>
    </div>
  );
}
