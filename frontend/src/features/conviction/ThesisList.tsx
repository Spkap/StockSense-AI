import { FileText, Plus } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { cn } from '../../utils/cn';
import type { Thesis } from '../../types/thesis';

interface ThesisListProps {
  theses: Thesis[];
  selectedThesisId: string | null;
  isLoading: boolean;
  onSelectThesis: (thesisId: string) => void;
  onCreateFromResearch: () => void;
}

const convictionStyles: Record<Thesis['conviction_level'], string> = {
  high: 'border-success/25 bg-success/10 text-success',
  medium: 'border-warning/25 bg-warning/10 text-warning',
  low: 'border-border bg-secondary text-muted-foreground',
};

const statusStyles: Record<Thesis['status'], string> = {
  active: 'border-success/25 bg-success/10 text-success',
  validated: 'border-primary/25 bg-primary/10 text-primary',
  invalidated: 'border-destructive/25 bg-destructive/10 text-destructive',
  exited: 'border-border bg-secondary text-muted-foreground',
};

export default function ThesisList({
  theses,
  selectedThesisId,
  isLoading,
  onSelectThesis,
  onCreateFromResearch,
}: ThesisListProps) {
  return (
    <section className="rounded-xl border border-border/60 bg-card/60 backdrop-blur-md shadow-sm">
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <div>
          <h2 className="text-sm font-semibold">Thesis memory</h2>
          <p className="text-xs text-muted-foreground">{theses.length} saved theses</p>
        </div>
        <Button type="button" size="sm" variant="outline" onClick={onCreateFromResearch}>
          <Plus />
          Create
        </Button>
      </div>

      <div className="max-h-[calc(100dvh-230px)] overflow-y-auto">
        {isLoading ? (
          <div className="grid gap-2 p-3">
            {[0, 1, 2].map((item) => (
              <div key={item} className="h-24 animate-pulse rounded-md bg-secondary" />
            ))}
          </div>
        ) : theses.length > 0 ? (
          <div className="grid gap-1 p-2">
            {theses.map((thesis) => {
              const selected = thesis.id === selectedThesisId;
              return (
                <button
                  key={thesis.id}
                  type="button"
                  onClick={() => onSelectThesis(thesis.id)}
                  className={cn(
                    'grid gap-2 rounded-xl px-4 py-3.5 text-left transition-all duration-300 ease-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                    selected ? 'bg-primary text-primary-foreground shadow-lux dark:shadow-lux-dark scale-[1.01]' : 'hover:bg-secondary/60 hover:shadow-sm hover:scale-[1.01] border border-transparent hover:border-border/50'
                  )}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-semibold">{thesis.ticker}</span>
                        <Badge
                          variant="outline"
                          className={cn('capitalize', selected ? 'border-primary-foreground/30 text-primary-foreground' : statusStyles[thesis.status])}
                        >
                          {thesis.status}
                        </Badge>
                      </div>
                      <p className={cn('mt-1 line-clamp-2 text-sm', selected ? 'text-primary-foreground/80' : 'text-muted-foreground')}>
                        {thesis.thesis_summary}
                      </p>
                    </div>
                    <FileText className={cn('mt-1 size-4 shrink-0', selected ? 'text-primary-foreground/70' : 'text-muted-foreground')} />
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge
                      variant="outline"
                      className={cn('capitalize', selected ? 'border-primary-foreground/30 text-primary-foreground' : convictionStyles[thesis.conviction_level])}
                    >
                      {thesis.conviction_level} conviction
                    </Badge>
                    <span className={cn('text-xs', selected ? 'text-primary-foreground/70' : 'text-muted-foreground')}>
                      Updated {new Date(thesis.updated_at).toLocaleDateString()}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        ) : (
          <div className="grid gap-3 p-4 text-sm text-muted-foreground">
            <p>No thesis memory yet.</p>
            <Button type="button" onClick={onCreateFromResearch}>
              Create thesis from research
            </Button>
          </div>
        )}
      </div>
    </section>
  );
}
