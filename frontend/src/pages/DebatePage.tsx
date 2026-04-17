import { useMemo, useRef, useState } from 'react';
import { ArrowLeft, Loader2, Play, RadioTower, RefreshCw, Scale } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { useStreamingDebate } from '../hooks/useStreamingDebate';
import { useDebateAnalysis } from '../api/debate';
import TickerInput, { type TickerInputRef } from '../components/TickerInput';
import QuickSelect from '../components/QuickSelect';
import DebateView from '../components/DebateView';
import { cn } from '../utils/cn';

interface DebatePageProps {
  onBack: () => void;
  initialTicker?: string | null;
}

const PHASE_LABELS: Record<string, string> = {
  debate_started: 'Preparing debate',
  tool_started: 'Collecting evidence',
  bull_drafting: 'Bull case drafting',
  bear_drafting: 'Bear case drafting',
  rebuttal_round: 'Cross-examination',
  synthesis_started: 'Synthesizing verdict',
  debate_completed: 'Complete',
};

export default function DebatePage({ onBack, initialTicker }: DebatePageProps) {
  const tickerInputRef = useRef<TickerInputRef>(null);
  const streaming = useStreamingDebate();
  const oneShotDebate = useDebateAnalysis();
  const [selectedTicker, setSelectedTicker] = useState<string | null>(initialTicker ?? null);

  const debateData = streaming.finalData || oneShotDebate.data?.data || null;
  const activePhase = useMemo(() => {
    if (!streaming.currentPhase) return null;
    return PHASE_LABELS[streaming.currentPhase] ?? streaming.currentPhase;
  }, [streaming.currentPhase]);

  const startStreamingDebate = (ticker: string) => {
    setSelectedTicker(ticker);
    oneShotDebate.reset();
    streaming.startDebate(ticker);
  };

  const startOneShotDebate = async (ticker: string) => {
    setSelectedTicker(ticker);
    streaming.reset();
    await oneShotDebate.mutateAsync(ticker);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-8 animate-in fade-in duration-500">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="space-y-2">
          <button onClick={onBack} className="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Debate Lab</h1>
            <p className="text-muted-foreground">Run a bull-vs-bear debate and inspect the probability-weighted verdict.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => selectedTicker && startOneShotDebate(selectedTicker)} disabled={!selectedTicker || oneShotDebate.isPending || streaming.isStreaming} className="gap-2">
            {oneShotDebate.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            One-shot Debate
          </Button>
          <Button onClick={() => selectedTicker && startStreamingDebate(selectedTicker)} disabled={!selectedTicker || streaming.isStreaming || oneShotDebate.isPending} className="gap-2">
            {streaming.isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <RadioTower className="h-4 w-4" />}
            Stream Debate
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-8">
          <TickerInput ref={tickerInputRef} onAnalyze={startStreamingDebate} disabled={streaming.isStreaming || oneShotDebate.isPending} />
        </div>
        <div className="lg:col-span-4">
          <QuickSelect onSelect={startStreamingDebate} disabled={streaming.isStreaming || oneShotDebate.isPending} />
        </div>
      </div>

      {(streaming.isStreaming || activePhase) && (
        <Card className="border-border/50 bg-card shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Scale className="h-5 w-5 text-primary" />
                  {selectedTicker || 'Debate'} in progress
                </CardTitle>
                <CardDescription>{activePhase || 'Waiting for first event...'}</CardDescription>
              </div>
              <Button variant="outline" size="sm" onClick={streaming.stopDebate} disabled={!streaming.isStreaming}>
                Stop
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="h-2 overflow-hidden rounded-full bg-secondary">
              <div className="h-full bg-primary transition-all duration-500" style={{ width: `${Math.round(streaming.progress * 100)}%` }} />
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              {streaming.phases.map((phase) => (
                <div
                  key={phase.id}
                  className={cn(
                    'rounded-xl border px-4 py-3 text-sm transition-colors',
                    phase.status === 'complete' && 'border-success/20 bg-success/10 text-success',
                    phase.status === 'active' && 'border-primary/20 bg-primary/10 text-primary',
                    phase.status === 'pending' && 'border-border/50 bg-background/60 text-muted-foreground'
                  )}
                >
                  <div className="font-medium">{phase.label}</div>
                  {phase.message && <div className="mt-1 text-xs opacity-80">{phase.message}</div>}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {oneShotDebate.error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
          Debate failed: {oneShotDebate.error.message}
        </div>
      )}

      {streaming.error && (
        <div className="rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive">
          Debate failed: {streaming.error}
        </div>
      )}

      {debateData ? (
        <DebateView data={debateData} />
      ) : (
        <Card className="border-dashed border-border/60 bg-card/60">
          <CardContent className="flex flex-col items-center justify-center py-20 text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Scale className="h-8 w-8" />
            </div>
            <h3 className="text-lg font-semibold">No debate yet</h3>
            <p className="mt-2 max-w-xl text-sm text-muted-foreground">
              Pick a ticker to generate a structured bull-vs-bear debate with rebuttals, scenario probabilities, and decisive factors.
            </p>
          </CardContent>
        </Card>
      )}

      {debateData && (
        <div className="flex justify-end">
          <Button variant="outline" onClick={() => selectedTicker && startStreamingDebate(selectedTicker)} disabled={!selectedTicker || streaming.isStreaming}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Re-run streamed debate
          </Button>
        </div>
      )}
    </div>
  );
}
