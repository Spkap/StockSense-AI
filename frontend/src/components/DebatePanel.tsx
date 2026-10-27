import { useEffect, useRef, useState } from 'react';
import { AlertCircle, ArrowDownRight, ArrowUpRight, Scale } from 'lucide-react';
import { Button } from './ui/button';
import type { DebateAnalysisResult, Rebuttal } from '../types/debate';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../utils/supabase';
import { API_BASE_URL } from '../config/env';

const API_URL = API_BASE_URL;

type StreamEvent = { type: string; message?: string; progress?: number; data?: unknown };

function validResult(value: unknown, ticker: string): value is DebateAnalysisResult {
  if (!value || typeof value !== 'object') return false;
  const d = value as DebateAnalysisResult;
  const p = d.verdict?.scenario_probabilities;
  return d.ticker === ticker && !!d.bull_case && !!d.bear_case && !!d.verdict &&
    typeof d.bull_case.thesis === 'string' && typeof d.bear_case.thesis === 'string' &&
    !!p && [p.bull, p.base, p.bear].every(n => typeof n === 'number' && Number.isFinite(n) && n >= 0 && n <= 1) &&
    Math.abs(p.bull + p.base + p.bear - 1) <= 0.05 &&
    Array.isArray(d.bull_case.catalysts) && Array.isArray(d.bear_case.risks) &&
    Array.isArray(d.rebuttals?.bear_to_bull) && Array.isArray(d.rebuttals?.bull_to_bear);
}

function Case({ title, thesis, points, rebuttals, bullish }: { title: string; thesis: string; points: string[]; rebuttals: Rebuttal[]; bullish: boolean }) {
  const Icon = bullish ? ArrowUpRight : ArrowDownRight;
  return <section className="border border-border-base bg-surface-1 rounded-sm overflow-hidden min-w-0">
    <div className="flex items-center gap-2 border-b border-border-base bg-surface-2 px-5 py-3">
      <Icon className={bullish ? 'h-4 w-4 text-bull' : 'h-4 w-4 text-bear'} />
      <h3 className="font-mono text-sm font-bold text-txt-primary">{title}</h3>
    </div>
    <div className="p-5 sm:p-6 space-y-6">
      <p className="research-copy text-txt-primary">{thesis}</p>
      {points.length > 0 && <div><h4 className="font-mono text-micro uppercase tracking-widest text-txt-muted mb-3">{bullish ? 'Potential catalysts' : 'Key risks'}</h4><ul className="space-y-3">{points.map((point, i) => <li key={i} className="research-copy text-txt-secondary border-l-2 border-border-strong pl-3">{point}</li>)}</ul></div>}
      {rebuttals.length > 0 && <div className="border-t border-border-base pt-5"><h4 className="font-mono text-micro uppercase tracking-widest text-accent mb-3">Challenge from the {bullish ? 'bear' : 'bull'} case</h4><div className="space-y-4">{rebuttals.map((item, i) => <div key={i}><p className="text-sm text-txt-muted">{item.target_claim}</p><p className="research-copy text-txt-secondary mt-1">{item.counter_argument}</p></div>)}</div></div>}
    </div>
  </section>;
}

export default function DebatePanel({ ticker }: { ticker: string }) {
  const { user } = useAuth();
  const owner = user?.id || null;
  const source = useRef<AbortController | null>(null);
  const [status, setStatus] = useState<'loading' | 'idle' | 'running' | 'done' | 'error'>('loading');
  const [message, setMessage] = useState('');
  const [warning, setWarning] = useState('');
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<DebateAnalysisResult | null>(null);

  async function headers(): Promise<Record<string, string>> {
    const { data: { session }, error } = supabase ? await supabase.auth.getSession() : { data: { session: null }, error: null };
    if (error || (session?.user.id || null) !== owner) throw new Error('Your session changed. Please try again.');
    return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
  }

  useEffect(() => {
    const controller = new AbortController();
    source.current = controller;
    setResult(null); setStatus('loading'); setWarning('');
    (async () => {
      try {
        const auth = await headers();
        if (controller.signal.aborted) return;
        const response = await fetch(`${API_URL}/debate/${encodeURIComponent(ticker)}`, { headers: auth, signal: controller.signal });
        if (!response.ok) throw new Error('Saved debate is temporarily unavailable.');
        const payload = await response.json();
        if (controller.signal.aborted) return;
        if (payload.data != null && !validResult(payload.data, ticker)) throw new Error('The saved debate is incomplete. Please run it again.');
        setResult(payload.data); setStatus(payload.data ? 'done' : 'idle');
      } catch (error) {
        if (!controller.signal.aborted) { setMessage(error instanceof Error ? error.message : 'Could not load the saved debate.'); setStatus('error'); }
      }
    })();
    return () => { controller.abort(); source.current?.abort(); source.current = null; };
  }, [ticker, owner]);

  function stop() {
    source.current?.abort(); source.current = null;
    setStatus(result ? 'done' : 'idle'); setMessage('');
  }
  async function start() {
    source.current?.abort();
    const controller = new AbortController(); source.current = controller;
    setProgress(0); setMessage('Connecting…'); setStatus('running');
    try {
      const auth = await headers();
      if (controller.signal.aborted) return;
      const response = await fetch(`${API_URL}/analyze/debate/${encodeURIComponent(ticker)}/stream`, { headers: auth, signal: controller.signal });
      if (!response.ok || !response.body) throw new Error('The debate could not connect. Please try again.');
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '', terminal = false;
      while (!terminal) {
        const chunk = await reader.read();
        if (controller.signal.aborted || source.current !== controller) return;
        buffer += decoder.decode(chunk.value, { stream: !chunk.done });
        const blocks = buffer.split(/\r?\n\r?\n/); buffer = blocks.pop() || '';
        for (const block of blocks) {
          const line = block.split(/\r?\n/).find(item => item.startsWith('data:'));
          if (!line) continue;
          const item: StreamEvent = JSON.parse(line.slice(5).trim());
          if (typeof item.progress === 'number' && Number.isFinite(item.progress)) setProgress(Math.max(0, Math.min(1, item.progress)));
          if (item.message) setMessage(item.message);
          if (item.type === 'error') throw new Error('The debate could not be completed. Your previous saved debate is unchanged.');
          if (item.type === 'debate_completed') {
            terminal = true;
            if (!validResult(item.data, ticker)) throw new Error('The debate returned incomplete results. Check your saved debate before trying again.');
            const completed = item.data as DebateAnalysisResult & { cache_saved?: boolean; cache_warning?: string };
            setResult(completed); setWarning(completed.cache_saved ? '' : completed.cache_warning || 'The debate could not be saved.'); setStatus('done');
            break;
          }
        }
        if (chunk.done) break;
      }
      if (!terminal) throw new Error('The debate connection ended early. Check your saved debate before trying again.');
      if (source.current === controller) source.current = null;
    } catch (error) {
      if (!controller.signal.aborted && source.current === controller) { source.current = null; setMessage(error instanceof Error ? error.message : 'The debate could not be completed.'); setStatus('error'); }
    }
  }
  const probabilities = result?.verdict.scenario_probabilities;
  return <div className="space-y-6">
    <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border-base bg-surface-2 px-5 py-4">
        <div className="flex items-center gap-3"><Scale className="h-4 w-4 text-accent" /><div><h2 className="font-mono text-sm font-bold text-txt-primary">Bull–bear debate <span className="text-txt-muted font-normal">/ {ticker}</span></h2><p className="text-sm text-txt-secondary mt-1">Two perspectives. One synthesis.</p></div></div>
        {status !== 'running' && <Button disabled={status === 'loading'} onClick={start}>{result ? 'Run again' : 'Start debate'}</Button>}
      </div>
      <div className="px-5 py-4 space-y-2 text-sm leading-relaxed text-txt-secondary">
        <p>Separate AI analysts build opposing cases, challenge each other, and synthesize the arguments. A run may take a minute or more.</p>
        <p>Model-generated scenarios and confidence are uncalibrated assessments, not verified forecasts or investment advice. {owner ? 'Your latest debate is saved with your research.' : 'The latest debate is shared with guests.'} Refreshing research keeps it; removing research deletes it.</p>
      </div>
      {status === 'loading' && <p role="status" className="px-5 pb-4 text-sm text-txt-muted">Loading saved debate…</p>}
      {result && status !== 'loading' && <p className="px-5 pb-4 text-sm text-txt-muted">{warning ? 'Current result is not saved.' : 'Saved debate'}</p>}
      {warning && <p role="alert" className="px-5 pb-4 text-sm text-accent">{warning}</p>}
      {status === 'running' && <div className="border-t border-border-base px-5 py-4 space-y-3" role="status" aria-live="polite"><div className="flex justify-between gap-4 text-sm text-txt-primary"><span>{message}</span><span className="text-accent font-mono">{Math.round(progress * 100)}%</span></div><div className="h-1 bg-surface-3"><div className="h-full bg-accent transition-all" style={{ width: `${progress * 100}%` }} /></div><Button variant="outline" onClick={stop}>Cancel</Button></div>}
      {status === 'error' && <div role="alert" className="border-t border-bear/30 px-5 py-4 flex gap-2 text-sm text-bear"><AlertCircle className="h-4 w-4 shrink-0" />{message}</div>}
    </div>
    {result && probabilities && <>
      <section className="border border-border-base bg-surface-1 rounded-sm p-5 sm:p-6 space-y-4">
        <div><h3 className="font-mono text-sm font-bold text-txt-primary">Synthesis</h3><p className="research-copy text-txt-secondary mt-3 max-w-[80ch]">{result.verdict.debate_summary?.synthesis || 'No synthesis was returned.'}</p></div>
        <div className="border-t border-border-base pt-4"><p className="text-micro font-mono uppercase tracking-widest text-txt-muted mb-3">Model-generated scenario estimates</p><div className="grid grid-cols-3 gap-2">{([['Bull', probabilities.bull], ['Base', probabilities.base], ['Bear', probabilities.bear]] as const).map(([label, value]) => <div key={label} className="border border-border-base bg-surface-2 p-3"><p className="text-sm text-txt-secondary">{label}</p><p className="text-xl font-mono text-txt-primary mt-1">{Math.round(value * 100)}%</p></div>)}</div><p className="text-sm text-txt-muted mt-3">These are model judgments, not measured probabilities of future prices.</p></div>
      </section>
      <div className="grid md:grid-cols-2 gap-4"><Case title="Bull case" thesis={result.bull_case.thesis} points={result.bull_case.catalysts.map(x => x.description)} rebuttals={result.rebuttals.bear_to_bull} bullish /><Case title="Bear case" thesis={result.bear_case.thesis} points={result.bear_case.risks.map(x => x.description)} rebuttals={result.rebuttals.bull_to_bear} bullish={false} /></div>
      {(result.verdict.decisive_factors?.length > 0 || result.verdict.unresolved_questions?.length > 0) && <section className="border border-border-base bg-surface-1 p-5 sm:p-6 grid md:grid-cols-2 gap-6">{([['Decisive factors', result.verdict.decisive_factors], ['Open questions', result.verdict.unresolved_questions]] as const).map(([label, items]) => <div key={label}><h3 className="font-mono text-sm font-bold text-txt-primary mb-3">{label}</h3><ul className="space-y-2">{(items || []).map((item, i) => <li key={i} className="research-copy text-txt-secondary">{item}</li>)}</ul></div>)}</section>}
    </>}
  </div>;
}
