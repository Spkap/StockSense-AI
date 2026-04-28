import { useEffect, useMemo, useState, type FormEvent } from 'react';
import { Loader2, Save, Search, Square, Wand2 } from 'lucide-react';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useCreateThesis } from '../../api/theses';
import { getResearchRoomThesisDraft } from '../../api/researchRoom';
import { useAuth } from '../../context/AuthContext';
import { useResearchRoomStream } from '../../hooks/useResearchRoomStream';
import type { CreateThesisRequest, Thesis } from '../../types/thesis';
import type { ResearchEvidenceItem, ResearchThesisDraft } from '../../types/researchRoom';
import ResearchEvidenceDrawer from './ResearchEvidenceDrawer';
import ResearchRoomLanes from './ResearchRoomLanes';

interface ResearchRoomProps {
  initialTicker?: string;
  onThesisCreated: (thesis: Thesis) => void;
}

const DEFAULT_QUESTION = "Is this company's current market narrative supported by the evidence?";

function draftToRequest(draft: ResearchThesisDraft): CreateThesisRequest {
  return {
    ticker: draft.ticker,
    thesis_summary: draft.thesis_summary,
    conviction_level: draft.conviction_level,
    kill_criteria: draft.kill_criteria,
    time_horizon: draft.time_horizon,
    thesis_type: draft.thesis_type,
    origin_analysis_snapshot: {
      sentiment: draft.conviction_level,
      confidence: draft.conviction_level === 'high' ? 0.8 : draft.conviction_level === 'medium' ? 0.55 : 0.3,
      key_themes: draft.evidence_refs,
      timestamp: new Date().toISOString(),
    },
  };
}

export default function ResearchRoom({ initialTicker = '', onThesisCreated }: ResearchRoomProps) {
  const { user } = useAuth();
  const stream = useResearchRoomStream();
  const createThesis = useCreateThesis();
  const [ticker, setTicker] = useState(initialTicker);
  const [question, setQuestion] = useState(DEFAULT_QUESTION);
  const [draft, setDraft] = useState<ResearchThesisDraft | null>(null);
  const [selectedEvidence, setSelectedEvidence] = useState<ResearchEvidenceItem | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isLoadingDraft, setIsLoadingDraft] = useState(false);

  useEffect(() => {
    if (initialTicker) setTicker(initialTicker);
  }, [initialTicker]);

  useEffect(() => {
    if (stream.finalData?.thesis_draft && !draft) {
      setDraft(stream.finalData.thesis_draft);
    }
  }, [draft, stream.finalData]);

  const normalizedTicker = ticker.trim().toUpperCase();
  const latestEvents = useMemo(() => stream.events.slice(-5), [stream.events]);

  async function handleRun(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setDraft(null);
    if (!normalizedTicker) {
      setFormError('Enter a ticker first.');
      return;
    }
    if (question.trim().length < 4) {
      setFormError('Ask a specific research question.');
      return;
    }
    await stream.start(normalizedTicker, question.trim());
  }

  async function handleLoadDraft() {
    setFormError(null);
    if (!stream.activeRunId) {
      setFormError('Run Research Room before drafting a thesis.');
      return;
    }
    setIsLoadingDraft(true);
    try {
      const nextDraft = await getResearchRoomThesisDraft(stream.activeRunId);
      setDraft(nextDraft);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Unable to load thesis draft.');
    } finally {
      setIsLoadingDraft(false);
    }
  }

  async function handleSaveThesis() {
    setFormError(null);
    if (!user) {
      setFormError('Sign in to save thesis memory.');
      return;
    }
    if (!draft) {
      setFormError('Draft a thesis before saving.');
      return;
    }
    if (draft.thesis_summary.trim().length < 10) {
      setFormError('Thesis summary is too short.');
      return;
    }
    const thesis = await createThesis.mutateAsync(draftToRequest(draft));
    onThesisCreated(thesis);
  }

  return (
    <div className="grid gap-4">
      <section className="rounded-lg border border-border/60 bg-card/60 p-5">
        <form onSubmit={handleRun} className="grid gap-4 lg:grid-cols-[180px_minmax(0,1fr)_auto] lg:items-end">
          <label className="grid gap-2 text-sm font-medium">
            Ticker
            <Input
              value={ticker}
              onChange={(event) => setTicker(event.target.value.toUpperCase())}
              placeholder="AMD"
              className="font-mono uppercase"
            />
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Research question
            <Input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Is AMD's AI server thesis real, or is the market over-narrating it?"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" disabled={stream.isStreaming}>
              {stream.isStreaming ? <Loader2 className="animate-spin" /> : <Search />}
              Run
            </Button>
            {stream.isStreaming ? (
              <Button type="button" variant="outline" onClick={() => void stream.stop()}>
                <Square />
                Stop
              </Button>
            ) : null}
          </div>
        </form>

        <div className="mt-4 grid gap-3 md:grid-cols-[minmax(0,1fr)_260px] md:items-start">
          <div className="grid gap-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium">Run progress</span>
              <span className="font-mono text-xs text-muted-foreground">{Math.round(stream.progress * 100)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-secondary">
              <div className="h-full bg-primary transition-all" style={{ width: `${Math.round(stream.progress * 100)}%` }} />
            </div>
            <div className="flex flex-wrap gap-2">
              {stream.phase ? <Badge variant="outline">{stream.phase}</Badge> : null}
              {stream.activeRunId ? <Badge variant="secondary" className="font-mono">{stream.activeRunId.slice(0, 8)}</Badge> : null}
            </div>
          </div>

          <div className="grid gap-2 rounded-lg border border-border/70 bg-background px-3 py-2">
            {latestEvents.length ? latestEvents.map(event => (
              <div key={`${event.type}-${event.progress}`} className="flex items-center justify-between gap-2 text-xs">
                <span className="truncate">{event.message}</span>
                <span className="font-mono text-muted-foreground">{event.type}</span>
              </div>
            )) : <p className="text-xs text-muted-foreground">No run events yet.</p>}
          </div>
        </div>

        {stream.error || formError ? (
          <div className="mt-4 rounded-md border border-destructive/25 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {formError ?? stream.error}
          </div>
        ) : null}
      </section>

      <ResearchRoomLanes events={stream.events} finalData={stream.finalData} onEvidenceSelect={setSelectedEvidence} />

      <section className="rounded-lg border border-border/60 bg-card/60 p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold">Draft thesis</h2>
            <p className="text-sm text-muted-foreground">Convert the memo into thesis memory after reviewing receipts.</p>
          </div>
          <Button
            type="button"
            variant="outline"
            disabled={!stream.activeRunId || isLoadingDraft}
            onClick={() => void handleLoadDraft()}
          >
            {isLoadingDraft ? <Loader2 className="animate-spin" /> : <Wand2 />}
            Draft thesis
          </Button>
        </div>

        <div className="mt-4 grid gap-4">
          <label className="grid gap-2 text-sm font-medium">
            Thesis summary
            <textarea
              value={draft?.thesis_summary ?? ''}
              onChange={(event) => setDraft(prev => prev ? { ...prev, thesis_summary: event.target.value } : prev)}
              rows={4}
              placeholder="Run Research Room, then draft a thesis."
              className="min-h-28 w-full resize-y rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </label>

          <div className="grid gap-3 md:grid-cols-3">
            <label className="grid gap-2 text-sm font-medium">
              Conviction
              <select
                value={draft?.conviction_level ?? 'medium'}
                onChange={(event) => setDraft(prev => prev ? { ...prev, conviction_level: event.target.value as ResearchThesisDraft['conviction_level'] } : prev)}
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
                value={draft?.time_horizon ?? 'medium'}
                onChange={(event) => setDraft(prev => prev ? { ...prev, time_horizon: event.target.value as ResearchThesisDraft['time_horizon'] } : prev)}
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
                value={draft?.thesis_type ?? 'growth'}
                onChange={(event) => setDraft(prev => prev ? { ...prev, thesis_type: event.target.value as ResearchThesisDraft['thesis_type'] } : prev)}
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

          <label className="grid gap-2 text-sm font-medium">
            Kill criteria
            <textarea
              value={(draft?.kill_criteria ?? []).join('\n')}
              onChange={(event) => setDraft(prev => prev ? {
                ...prev,
                kill_criteria: event.target.value.split('\n').map(item => item.trim()).filter(Boolean),
              } : prev)}
              rows={4}
              placeholder="One criterion per line"
              className="min-h-24 w-full resize-y rounded-lg border border-input bg-background px-3 py-2 font-mono text-sm outline-none focus:ring-2 focus:ring-ring"
            />
          </label>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" disabled={!draft || createThesis.isPending} onClick={() => void handleSaveThesis()}>
              {createThesis.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              Save thesis
            </Button>
            {!user ? <Badge variant="outline">Sign in required</Badge> : null}
            {draft?.evidence_refs.length ? (
              <span className="text-xs text-muted-foreground">Refs: {draft.evidence_refs.join(', ')}</span>
            ) : null}
          </div>

          {createThesis.isError ? (
            <p className="text-sm text-destructive">
              {createThesis.error instanceof Error ? createThesis.error.message : 'Failed to save thesis.'}
            </p>
          ) : null}
        </div>
      </section>

      <ResearchEvidenceDrawer evidence={selectedEvidence} onClose={() => setSelectedEvidence(null)} />
    </div>
  );
}
