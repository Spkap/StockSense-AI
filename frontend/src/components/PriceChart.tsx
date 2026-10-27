import { useEffect, useId, useMemo, useRef, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { Activity, ArrowDownRight, ArrowUpRight, ChartNoAxesCombined } from 'lucide-react';
import type { PriceDataPoint } from '../types/api';
import { cn } from '../utils/cn';
import { API_BASE_URL } from '../config/env';

type Range = '1W' | '1M' | '1Y' | 'ALL';
type ChartPoint = { date: string; close: number; volume: number | null };

const formatDate = (date: string, options: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric', year: 'numeric' }) =>
  new Date(`${date}T00:00:00Z`).toLocaleDateString('en-US', { ...options, timeZone: 'UTC' });
const formatNumber = (number: number) => number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function PriceTooltip({ active, payload, currency }: { active?: boolean; payload?: ReadonlyArray<{ payload?: ChartPoint }>; currency?: string }) {
  const point = payload?.[0]?.payload;
  if (!active || !point) return null;
  return <div className="border border-border-strong bg-[#151515] px-4 py-3 font-mono shadow-xl" role="status">
    <p className="text-micro text-txt-muted">{formatDate(point.date)}</p>
    <p className="mt-1 text-lg text-txt-primary">{formatNumber(point.close)} <span className="text-micro text-txt-muted">{currency || ''}</span></p>
    <p className="mt-1 text-micro text-txt-secondary">Volume {point.volume == null ? '—' : point.volume.toLocaleString('en-US')}</p>
  </div>;
}

export default function PriceChart({ points, currency, ticker }: { points: PriceDataPoint[]; currency?: string; ticker: string }) {
  const [range, setRange] = useState<Range>('ALL');
  const [yearData, setYearData] = useState<PriceDataPoint[] | null>(null);
  const [yearLoading, setYearLoading] = useState(false);
  const [yearError, setYearError] = useState<string | null>(null);
  const requestRef = useRef<AbortController | null>(null);
  useEffect(() => {
    setRange('ALL'); setYearData(null); setYearLoading(false); setYearError(null);
    return () => { requestRef.current?.abort(); requestRef.current = null; };
  }, [ticker]);
  const chooseRange = async (next: Range) => {
    requestRef.current?.abort(); requestRef.current = null;
    setYearError(null);
    if (next !== '1Y' || yearData) { setYearLoading(false); setRange(next); return; }
    const controller = new AbortController(); requestRef.current = controller; setYearLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/prices/${encodeURIComponent(ticker.toUpperCase())}`, { signal: controller.signal });
      if (!response.ok) throw new Error('Price history unavailable');
      const body = await response.json();
      if (body.ticker !== ticker.toUpperCase() || body.period !== '1y' || body.adjusted !== true || !Array.isArray(body.price_data) || !body.price_data.some((p: PriceDataPoint) => /^\d{4}-\d{2}-\d{2}$/.test(String(p.Date)) && Number.isFinite(Date.parse(`${p.Date}T00:00:00Z`)) && typeof p.Close === 'number' && Number.isFinite(p.Close))) throw new Error('Invalid price history');
      if (requestRef.current !== controller) return;
      setYearData(body.price_data); setRange('1Y');
    } catch {
      if (!controller.signal.aborted) setYearError('Could not load one-year price history. Please try again.');
    } finally {
      if (requestRef.current === controller) { requestRef.current = null; setYearLoading(false); }
    }
  };
  const gradientId = `price-gradient-${useId().replace(/:/g, '')}`;
  const data = useMemo(() => {
    const unique = new Map<string, ChartPoint>();
    for (const point of (range === '1Y' ? yearData : points) || []) {
      const date = String(point.Date || '').slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(date) || !Number.isFinite(Date.parse(`${date}T00:00:00Z`)) || typeof point.Close !== 'number' || !Number.isFinite(point.Close)) continue;
      unique.set(date, { date, close: point.Close, volume: typeof point.Volume === 'number' && Number.isFinite(point.Volume) ? point.Volume : null });
    }
    return [...unique.values()].sort((a, b) => a.date.localeCompare(b.date));
  }, [points, range, yearData]);
  const visible = useMemo(() => {
    if (!data.length || range === 'ALL' || range === '1Y') return data;
    const last = Date.parse(`${data[data.length - 1].date}T00:00:00Z`);
    const threshold = last - (range === '1W' ? 7 : 31) * 86400000;
    return data.filter(point => Date.parse(`${point.date}T00:00:00Z`) >= threshold);
  }, [data, range]);
  const first = visible[0];
  const latest = visible[visible.length - 1];
  const change = first && latest && visible.length > 1 ? latest.close - first.close : null;
  const changePercent = change != null && first.close !== 0 ? change / first.close * 100 : null;
  const high = visible.length ? Math.max(...visible.map(point => point.close)) : null;
  const low = visible.length ? Math.min(...visible.map(point => point.close)) : null;
  const lastVolume = latest?.volume;
  const movement = change == null ? null : change >= 0;

  if (!data.length) return <section className="border border-border-base bg-surface-1 p-8 text-center" role="status"><ChartNoAxesCombined className="mx-auto mb-4 h-5 w-5 text-txt-muted" /><h3 className="font-mono text-lg text-txt-primary">Price history unavailable</h3><p className="mt-2 text-sm text-txt-secondary">No valid daily closing prices were saved with this research. Refresh the analysis to try again.</p></section>;

  return <section className="overflow-hidden border border-border-base bg-surface-1" aria-label={`${ticker} historical price chart`}>
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-base px-5 py-3 sm:px-6">
      <div className="flex items-center gap-2 font-mono text-micro uppercase tracking-widest text-txt-secondary"><Activity className="h-3.5 w-3.5 text-accent" /> Price history <span className="text-txt-muted">/</span> {ticker}</div>
      <span className="font-mono text-micro uppercase tracking-wider text-txt-muted">Daily close · {currency || 'Currency unavailable'}</span>
    </div>
    <div className="px-5 pt-6 sm:px-8 sm:pt-8">
      <div className="flex flex-wrap items-end justify-between gap-5">
        <div>
          <p className="font-mono text-micro uppercase tracking-widest text-txt-muted">Latest daily price <span className="text-txt-tertiary">/ {formatDate(latest.date)}</span></p>
          <div className="mt-2 flex flex-wrap items-baseline gap-3"><span className="font-mono text-4xl font-medium tracking-tight text-txt-primary sm:text-5xl">{formatNumber(latest.close)}</span><span className="font-mono text-sm text-txt-muted">{currency || ''}</span></div>
          <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-sm">
            {change != null && changePercent != null ? <><span className={cn('inline-flex items-center gap-1', movement ? 'text-bull' : 'text-bear')}>{movement ? <ArrowUpRight className="h-4 w-4" /> : <ArrowDownRight className="h-4 w-4" />}{change >= 0 ? '+' : ''}{formatNumber(change)} ({changePercent >= 0 ? '+' : ''}{formatNumber(changePercent)}%)</span><span className="text-txt-muted">over selected period</span></> : <span className="text-txt-muted">Change unavailable for a single data point</span>}
          </div>
        </div>
        <div className="flex gap-1 border border-border-base bg-canvas p-1" role="group" aria-label="Price chart time range">
          {(['1W', '1M', '1Y', 'ALL'] as const).map(option => <button key={option} type="button" aria-pressed={range === option} onClick={() => void chooseRange(option)} className={cn('min-h-9 min-w-11 px-3 font-mono text-micro transition-colors', range === option ? 'bg-surface-3 text-accent' : 'text-txt-muted hover:bg-surface-2 hover:text-txt-primary')}>{option === 'ALL' ? 'SAVED' : option}</button>)}
        </div>
      </div>
      {yearLoading && <p className="mt-4 text-sm text-txt-secondary" role="status">Loading one-year price history…</p>}
      {yearError && <p className="mt-4 text-sm text-bear" role="alert">{yearError}</p>}
      <div className="mt-7 flex items-center justify-between gap-3 border-t border-border-base pt-4 font-mono text-micro text-txt-muted"><span>ADJUSTED DAILY CLOSE</span><span>{formatDate(first.date, { month: 'short', day: 'numeric', year: 'numeric' })} — {formatDate(latest.date, { month: 'short', day: 'numeric', year: 'numeric' })}</span></div>
      {visible.length > 1 ? <div className="mt-2 h-[260px] w-full sm:h-[340px]" aria-label="Daily closing prices. Focus the chart and use left and right arrow keys to explore dates.">
        <ResponsiveContainer width="100%" height="100%"><AreaChart data={visible} margin={{ top: 16, right: 8, left: -12, bottom: 0 }} title={`${ticker} adjusted daily closing prices`} accessibilityLayer>
          <defs><linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#F5B400" stopOpacity={0.22} /><stop offset="95%" stopColor="#F5B400" stopOpacity={0.005} /></linearGradient></defs>
          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.07)" strokeDasharray="3 5" />
          <XAxis dataKey="date" tickFormatter={value => formatDate(value, { month: 'short', day: 'numeric' })} minTickGap={32} tickLine={false} axisLine={false} tick={{ fill: 'rgba(255,255,255,.55)', fontSize: 11, fontFamily: 'Geist Mono' }} dy={10} />
          <YAxis domain={['auto', 'auto']} tickFormatter={value => Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 })} width={64} tickLine={false} axisLine={false} tick={{ fill: 'rgba(255,255,255,.55)', fontSize: 11, fontFamily: 'Geist Mono' }} />
          <Tooltip content={<PriceTooltip currency={currency} />} cursor={{ stroke: 'rgba(245,180,0,.5)', strokeDasharray: '3 4' }} />
          <ReferenceLine y={first.close} stroke="rgba(255,255,255,.20)" strokeDasharray="3 5" />
          <Area type="linear" dataKey="close" stroke="#F5B400" strokeWidth={2.5} fill={`url(#${gradientId})`} dot={false} activeDot={{ r: 5, fill: '#F5B400', stroke: '#111', strokeWidth: 3 }} isAnimationActive={false} />
        </AreaChart></ResponsiveContainer>
      </div> : <div className="flex h-52 items-center justify-center text-center font-mono text-sm text-txt-muted">Only one closing price is available for this period.</div>}
      <div className="pb-5" />
    </div>
    <div className="grid grid-cols-2 border-t border-border-base sm:grid-cols-4">
      {[['Highest close', high == null ? '—' : formatNumber(high)], ['Lowest close', low == null ? '—' : formatNumber(low)], ['Latest volume', lastVolume == null ? '—' : lastVolume.toLocaleString('en-US')], ['Trading days', String(visible.length)]].map(([label, value]) => <div key={label} className="border-b border-r border-border-base px-5 py-4 last:border-r-0 sm:border-b-0 sm:px-6"><p className="font-mono text-micro uppercase tracking-wider text-txt-muted">{label}</p><p className="mt-2 font-mono text-base text-txt-primary">{value}</p></div>)}
    </div>
    <details className="border-t border-border-base px-5 py-4 sm:px-6"><summary className="cursor-pointer font-mono text-micro uppercase tracking-wider text-txt-secondary hover:text-txt-primary">View daily data</summary><div className="mt-4 max-h-72 overflow-auto"><table className="w-full text-left font-mono text-sm"><thead><tr className="border-b border-border-base text-txt-muted"><th className="py-2">Date</th><th>Close{currency ? ` (${currency})` : ''}</th><th>Volume</th></tr></thead><tbody>{[...visible].reverse().map(point => <tr key={point.date} className="border-b border-border-base text-txt-secondary"><td className="py-2 pr-3">{point.date}</td><td className="pr-3">{formatNumber(point.close)}</td><td>{point.volume == null ? '—' : point.volume.toLocaleString('en-US')}</td></tr>)}</tbody></table></div></details>
  </section>;
}
