import { useEffect, useState } from 'react';
import { Loader2, Save, Search, Square } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useCreateThesis } from '../../api/theses';
import { useAuth } from '../../context/AuthContext';
import { useStreamingAnalysis } from '../../hooks/useStreamingAnalysis';
import type { AnalysisData } from '../../types/api';
import type { CreateThesisRequest, Thesis } from '../../types/thesis';
import { buildAnalysisSnapshot } from './types';

interface ResearchIntakeProps {
  initialTicker?: string;
  onThesisCreated: (thesis: Thesis) => void;
}

function analysisFromStream(finalData: AnalysisData | null, partialData: Partial<AnalysisData>): AnalysisData | null {
  return finalData ?? (partialData.ticker && partialData.summary ? (partialData as AnalysisData) : null);
}

export default function ResearchIntake({ initialTicker = '', onThesisCreated }: ResearchIntakeProps) {
  const { user } = useAuth();
  const streaming = useStreamingAnalysis();
  const createThesis = useCreateThesis();
  const [ticker, setTicker] = useState(initialTicker);
  const [thesisSummary, setThesisSummary] = useState('');
  const [killCriteria, setKillCriteria] = useState('');
  const [convictionLevel, setConvictionLevel] = useState<CreateThesisRequest['conviction_level']>('medium');
  const [timeHorizon, setTimeHorizon] = useState<CreateThesisRequest['time_horizon']>('medium');
  const [thesisType, setThesisType] = useState<CreateThesisRequest['thesis_type']>('growth');
  const [error, setError] = useState<string | null>(null);
  const analysis = analysisFromStream(streaming.finalData, streaming.partialData);

  useEffect(() => {
    if (initialTicker) setTicker(initialTicker);
  }, [initialTicker]);

  useEffect(() => {
    if (streaming.finalData && !thesisSummary) {
      setThesisSummary(streaming.finalData.summary || streaming.finalData.sentiment_report || '');
    }
    if (streaming.finalData && !killCriteria) {
      const criteria = [
        ...(streaming.finalData.hidden_risks ?? []),
        ...(streaming.finalData.would_change_mind ?? []),
      ].slice(0, 5);
      setKillCriteria(criteria.join('\n'));
    }
  }, [killCriteria, streaming.finalData, thesisSummary]);

  const normalizedTicker = ticker.trim().toUpperCase();

  async function handleAnalyze(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (!normalizedTicker) {
      setError('Enter a ticker first.');
      return;
    }
    await streaming.startAnalysis(normalizedTicker);
  }

  async function handleSaveThesis() {
    setError(null);
    if (!user) {
      setError('Sign in to save thesis memory.');
      return;
    }
    if (!analysis) {
      setError('Run research before saving a thesis.');
      return;
    }
    if (thesisSummary.trim().length < 10) {
      setError('Write a thesis summary before saving.');
      return;
    }

    const payload: CreateThesisRequest = {
      ticker: analysis.ticker || normalizedTicker,
      thesis_summary: thesisSummary.trim(),
      conviction_level: convictionLevel,
      kill_criteria: killCriteria
        .split('\n')
        .map((criterion) => criterion.trim())
        .filter(Boolean),
      time_horizon: timeHorizon,
      thesis_type: thesisType,
      origin_analysis_id: analysis.id,
      origin_analysis_snapshot: buildAnalysisSnapshot(analysis),
    };

    const thesis = await createThesis.mutateAsync(payload);
    onThesisCreated(thesis);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
      <section className="rounded-2xl border border-border/60 bg-card/60 p-5 backdrop-blur-md shadow-sm">
        <form onSubmit={handleAnalyze} className="grid gap-4">
          <div className="grid gap-2">
            <label htmlFor="research-ticker" className="text-sm font-medium">
              Ticker
            </label>
            <div className="flex gap-2">
              <Input
                id="research-ticker"
                value={ticker}
                onChange={(event) => setTicker(event.target.value.toUpperCase())}
                placeholder="AAPL"
                className="font-mono uppercase"
              />
              <Button type="submit" disabled={streaming.isStreaming}>
                {streaming.isStreaming ? <Loader2 className="animate-spin" /> : <Search />}
                Research
              </Button>
            </div>
          </div>

          {streaming.isStreaming ? (
            <Button type="button" variant="outline" className="w-fit" onClick={streaming.stopAnalysis}>
              <Square />
              Stop stream
            </Button>
          ) : null}

          <div className="grid gap-2 rounded-md border border-border/80 bg-secondary/35 p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium">Stream</span>
              <span className="font-mono text-xs text-muted-foreground">{Math.round(streaming.progress * 100)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-background">
              <div className="h-full bg-primary transition-all" style={{ width: `${Math.round(streaming.progress * 100)}%` }} />
            </div>
            <div className="grid gap-2">
              {streaming.events.slice(-6).map((event, index) => (
                <div key={`${event.type}-${index}`} className="rounded-md border border-border/70 bg-background px-3 py-2">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-medium">{event.message}</span>
                    <span className="font-mono text-xs text-muted-foreground">{event.tool ?? event.type}</span>
                  </div>
                </div>
              ))}
              {streaming.events.length === 0 ? <p className="text-sm text-muted-foreground">No research stream started.</p> : null}
            </div>
          </div>

          {streaming.error || error ? (
            <div className="rounded-md border border-destructive/25 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error ?? streaming.error}
            </div>
          ) : null}
        </form>
      </section>

      <section className="grid gap-4">
        <div className="rounded-2xl border border-border/60 bg-card/60 p-5 backdrop-blur-md shadow-lux dark:shadow-lux-dark">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold">Research summary</h2>
              <p className="text-sm text-muted-foreground">Use this to create or update thesis memory.</p>
            </div>
            {analysis ? (
              <Badge variant="outline" className="font-mono">
                {analysis.ticker}
              </Badge>
            ) : null}
          </div>

          {analysis ? (
            <div className="mt-4 grid gap-4">
              <div className="grid gap-2">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{analysis.overall_sentiment || 'Unknown sentiment'}</Badge>
                  <Badge variant="outline">{Math.round((analysis.overall_confidence ?? 0) * 100)}% confidence</Badge>
                  <Badge variant="outline">{analysis.source}</Badge>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">{analysis.summary || analysis.sentiment_report}</p>
              </div>

              {(analysis.key_themes ?? []).length > 0 ? (
                <div className="grid gap-2">
                  <h3 className="text-sm font-semibold">Evidence themes</h3>
                  <div className="grid gap-2">
                    {(analysis.key_themes ?? []).slice(0, 5).map((theme) => (
                      <div key={theme.theme} className="rounded-xl border border-border/40 bg-secondary/30 px-4 py-3">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="text-sm font-medium">{theme.theme}</span>
                          <Badge variant="outline">{theme.sentiment_direction}</Badge>
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">{theme.summary}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">Run ticker research to populate the thesis draft.</p>
          )}
        </div>

        <div className="rounded-2xl border border-border/60 bg-card/60 p-5 backdrop-blur-md shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-semibold">Save Thesis</h2>
            {!user ? <Badge variant="outline">Sign in required</Badge> : null}
          </div>
          <div className="mt-4 grid gap-4">
            <div className="grid gap-2">
              <label htmlFor="thesis-summary" className="text-sm font-medium">
                Thesis summary
              </label>
              <textarea
                id="thesis-summary"
                value={thesisSummary}
                onChange={(event) => setThesisSummary(event.target.value)}
                rows={5}
                placeholder="I believe this company will..."
                className="min-h-28 w-full resize-y rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              <label className="grid gap-2 text-sm font-medium">
                Conviction
                <select
                  value={convictionLevel}
                  onChange={(event) => setConvictionLevel(event.target.value as CreateThesisRequest['conviction_level'])}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>
              <label className="grid gap-2 text-sm font-medium">
                Horizon
                <select
                  value={timeHorizon}
                  onChange={(event) => setTimeHorizon(event.target.value as CreateThesisRequest['time_horizon'])}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="short">Short</option>
                  <option value="medium">Medium</option>
                  <option value="long">Long</option>
                </select>
              </label>
              <label className="grid gap-2 text-sm font-medium">
                Type
                <select
                  value={thesisType}
                  onChange={(event) => setThesisType(event.target.value as CreateThesisRequest['thesis_type'])}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="growth">Growth</option>
                  <option value="value">Value</option>
                  <option value="income">Income</option>
                  <option value="turnaround">Turnaround</option>
                  <option value="special_situation">Special Situation</option>
                </select>
              </label>
            </div>

            <div className="grid gap-2">
              <label htmlFor="kill-criteria" className="text-sm font-medium">
                Kill criteria
              </label>
              <textarea
                id="kill-criteria"
                value={killCriteria}
                onChange={(event) => setKillCriteria(event.target.value)}
                rows={4}
                placeholder="One criterion per line"
                className="min-h-24 w-full resize-y rounded-lg border border-input bg-background px-3 py-2 font-mono text-sm outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            <Button
              type="button"
              className="w-fit"
              disabled={createThesis.isPending || !analysis}
              onClick={() => void handleSaveThesis()}
            >
              {createThesis.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Save Thesis
            </Button>

            {createThesis.isError ? (
              <p className="text-sm text-destructive">
                {createThesis.error instanceof Error ? createThesis.error.message : 'Failed to save thesis.'}
              </p>
            ) : null}
          </div>
        </div>
      </section>
    </div>
  );
}
