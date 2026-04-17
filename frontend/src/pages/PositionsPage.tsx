import { useMemo, useState } from 'react';
import { ArrowLeft, BriefcaseBusiness, Plus, Search, Trash2, TrendingUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { useDeletePosition, usePositions } from '../api/user';
import PositionEditor from '../components/PositionEditor';
import type { Position } from '../types/api';
import { cn } from '../utils/cn';
import { useAuth } from '../context/AuthContext';

interface PositionsPageProps {
  onBack: () => void;
  onAnalyzeTicker: (ticker: string) => void;
  initialTicker?: string | null;
}

const POSITION_TYPE_STYLES = {
  long: 'bg-success/10 text-success border-success/20',
  short: 'bg-destructive/10 text-destructive border-destructive/20',
  watching: 'bg-secondary text-secondary-foreground border-border/40',
};

function formatNumber(value?: number | null) {
  if (typeof value !== 'number') return '—';
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
}

function PositionCard({
  position,
  onAnalyze,
  onDelete,
  deleting,
}: {
  position: Position;
  onAnalyze: (ticker: string) => void;
  onDelete: (positionId: string) => void;
  deleting: boolean;
}) {
  return (
    <Card className="border-border/50 bg-card shadow-sm transition-colors hover:border-primary/20">
      <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-lg font-bold text-primary">
            {position.ticker}
          </div>
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-semibold">{position.ticker}</h3>
              <span className={cn('inline-flex rounded-full border px-2.5 py-1 text-xs font-medium uppercase tracking-wider', POSITION_TYPE_STYLES[position.position_type])}>
                {position.position_type}
              </span>
            </div>
            <div className="grid gap-2 text-sm text-muted-foreground md:grid-cols-3">
              <span>Entry: {position.entry_date || '—'}</span>
              <span>Price: {position.entry_price != null ? `$${formatNumber(position.entry_price)}` : '—'}</span>
              <span>Shares: {formatNumber(position.current_shares)}</span>
            </div>
            {position.notes && <p className="max-w-2xl text-sm text-muted-foreground">{position.notes}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2 md:self-start">
          <Button variant="outline" size="sm" onClick={() => onAnalyze(position.ticker)} className="gap-2">
            <TrendingUp className="h-4 w-4" />
            Analyze
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(position.id)}
            disabled={deleting}
            className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
            title={`Delete ${position.ticker} position`}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function PositionsPage({ onBack, onAnalyzeTicker, initialTicker }: PositionsPageProps) {
  const { user } = useAuth();
  const { data, isLoading, error } = usePositions(!!user);
  const deletePosition = useDeletePosition();
  const [query, setQuery] = useState('');
  const [showEditor, setShowEditor] = useState(Boolean(initialTicker));
  const [editorTicker, setEditorTicker] = useState<string | null>(initialTicker ?? null);

  const positions = useMemo(() => {
    const all = data?.positions ?? [];
    if (!query.trim()) return all;
    const normalizedQuery = query.trim().toUpperCase();
    return all.filter((position) => position.ticker.includes(normalizedQuery) || position.notes?.toUpperCase().includes(normalizedQuery));
  }, [data?.positions, query]);

  if (!user) {
    return (
      <Card className="border-dashed border-border/60 bg-card/60">
        <CardContent className="flex flex-col items-center justify-center py-24 text-center">
          <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
            <BriefcaseBusiness className="h-8 w-8" />
          </div>
          <h3 className="text-lg font-semibold">Sign in to manage positions</h3>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            Positions are stored per-user through the backend, so you need to authenticate before tracking them.
          </p>
          <Button onClick={onBack} className="mt-6">Back to Dashboard</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <button onClick={onBack} className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Positions</h1>
            <p className="text-muted-foreground">Track long, short, and watchlist ideas against your analyses and theses.</p>
          </div>
        </div>
        <Button
          onClick={() => {
            setEditorTicker(initialTicker ?? null);
            setShowEditor(true);
          }}
          className="gap-2"
        >
          <Plus className="h-4 w-4" />
          Add Position
        </Button>
      </div>

      <Card className="border-border/50 bg-card shadow-sm">
        <CardHeader className="gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <CardTitle>Tracked Positions</CardTitle>
            <CardDescription>{data?.count ?? 0} positions across your portfolio and watchlist.</CardDescription>
          </div>
          <div className="relative w-full md:w-72">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter by ticker or notes"
              className="pl-10"
            />
          </div>
        </CardHeader>
      </Card>

      {error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
          Failed to load positions: {error.message}
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-4">
          {[1, 2, 3].map((index) => (
            <div key={index} className="h-28 animate-pulse rounded-xl bg-muted/40" />
          ))}
        </div>
      ) : positions.length === 0 ? (
        <Card className="border-dashed border-border/60 bg-card/60">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
              <BriefcaseBusiness className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold">No positions yet</h3>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Add long, short, or watchlist positions so you can connect analyses and theses to actual portfolio decisions.
            </p>
            <Button
              onClick={() => {
                setEditorTicker(initialTicker ?? null);
                setShowEditor(true);
              }}
              className="mt-6 gap-2"
            >
              <Plus className="h-4 w-4" />
              Add Your First Position
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {positions.map((position) => (
            <PositionCard
              key={position.id}
              position={position}
              onAnalyze={onAnalyzeTicker}
              onDelete={(positionId) => deletePosition.mutate(positionId)}
              deleting={deletePosition.isPending}
            />
          ))}
        </div>
      )}

      <PositionEditor
        isOpen={showEditor}
        initialTicker={editorTicker}
        onClose={() => {
          setShowEditor(false);
          setEditorTicker(null);
        }}
      />
    </div>
  );
}
