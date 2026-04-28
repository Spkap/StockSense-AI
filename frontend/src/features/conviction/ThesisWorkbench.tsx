import { useEffect, useMemo } from 'react';
import { Button } from '../../components/ui/button';
import { useAuth } from '../../context/AuthContext';
import { useTheses } from '../../api/theses';
import { sortThesesByUpdatedAt } from './types';
import ThesisDetail from './ThesisDetail';
import ThesisList from './ThesisList';

interface ThesisWorkbenchProps {
  selectedThesisId: string | null;
  onSelectThesis: (thesisId: string | null) => void;
  onCreateFromResearch: (ticker?: string) => void;
}

export default function ThesisWorkbench({ selectedThesisId, onSelectThesis, onCreateFromResearch }: ThesisWorkbenchProps) {
  const { user } = useAuth();
  const { data, isLoading, isError } = useTheses(undefined, Boolean(user));
  const theses = useMemo(() => sortThesesByUpdatedAt(data?.theses ?? []), [data?.theses]);
  const selectedThesis = theses.find((thesis) => thesis.id === selectedThesisId) ?? theses[0] ?? null;

  useEffect(() => {
    if (!selectedThesisId && selectedThesis) {
      onSelectThesis(selectedThesis.id);
    }
  }, [onSelectThesis, selectedThesis, selectedThesisId]);

  if (!user) {
    return (
      <section className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-sm p-4 md:p-5">
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(360px,0.8fr)] lg:items-center">
          <div className="grid gap-3">
          <h2 className="text-lg font-semibold">Sign in to load your thesis memory.</h2>
          <p className="text-sm text-muted-foreground">
            Thesis memory, evidence corrections, and kill alerts are stored against your account.
          </p>
          </div>
          <div className="grid gap-2 sm:grid-cols-3 lg:grid-cols-1">
            {[
              ['Memory', 'Saved thesis, criteria, status'],
              ['Checks', 'Latest verdict and source health'],
              ['Corrections', 'Evidence feedback history'],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3">
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
        <h2 className="text-lg font-semibold">Could not load thesis memory</h2>
        <p className="mt-2 text-sm">The backend rejected the thesis request.</p>
      </section>
    );
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <ThesisList
        theses={theses}
        selectedThesisId={selectedThesis?.id ?? null}
        isLoading={isLoading}
        onSelectThesis={onSelectThesis}
        onCreateFromResearch={() => onCreateFromResearch()}
      />
      {theses.length === 0 && !isLoading ? (
        <section className="rounded-2xl border border-border/60 bg-card/60 backdrop-blur-md shadow-sm p-6">
          <div className="grid max-w-2xl gap-4">
            <h2 className="text-lg font-semibold">No thesis memory yet</h2>
            <p className="text-sm text-muted-foreground">
              Start with ticker research, then save the thesis and kill criteria you want checked later.
            </p>
            <Button type="button" className="w-fit" onClick={() => onCreateFromResearch()}>
              Create thesis from research
            </Button>
          </div>
        </section>
      ) : (
        <ThesisDetail thesis={selectedThesis} onCreateFromResearch={onCreateFromResearch} />
      )}
    </div>
  );
}
