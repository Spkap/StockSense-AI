import { lazy, Suspense, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { RefreshCw, FileText, BarChart3, ShieldAlert, Newspaper, ChartNoAxesCombined, Scale } from 'lucide-react';
import { Button } from './ui/button';
import FundamentalsCard from './FundamentalsCard';
import ThesisEditor from './ThesisEditor';
import { useThesisForTicker } from '../api/theses';
import SkepticCard from './SkepticCard';
import SentimentCard from './SentimentCard';
import DebatePanel from './DebatePanel';
const PriceChart = lazy(() => import('./PriceChart'));
import type { AnalysisData } from '../types/api';
import { cn } from '../utils/cn';
import { useAuth } from '../context/AuthContext';

interface ResultsTabsProps {
  result: AnalysisData;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const tabs = [
  { id: 'thesis', label: 'Overview', icon: FileText },
  { id: 'news', label: 'News', icon: Newspaper },
  { id: 'prices', label: 'Prices', icon: ChartNoAxesCombined },
  { id: 'skeptic', label: 'Independent review', icon: ShieldAlert },
  { id: 'debate', label: 'Bull–bear debate', icon: Scale },
  { id: 'fundamentals', label: 'Financials', icon: BarChart3 },
];

const ResultsTabs = ({ result, onRefresh, isRefreshing }: ResultsTabsProps) => {
  const [activeTab, setActiveTab] = useState('thesis');
  const { user } = useAuth();
  const [showThesisEditor, setShowThesisEditor] = useState(false);
  const { data: thesisData, isFetching: isThesisLoading, error: thesisError } = useThesisForTicker(result.ticker);
  const existingThesis = thesisData?.theses[0] ?? null;
  const ageHours = result.cache_age_hours ?? Math.max(0, (Date.now() - new Date(result.timestamp).getTime()) / 3600000);
  const safeSourceUrl = (value?: string | null) => {
    try {
      const url = new URL(value || '');
      return ['https:', 'http:'].includes(url.protocol) && !url.username && !url.password ? url.href : null;
    } catch { return null; }
  };


  return (
    <div className="space-y-6">
      {Number.isFinite(ageHours) && <p className="text-sm text-txt-secondary">Research snapshot · {ageHours < 1 ? 'less than an hour old' : `${Math.round(ageHours)} ${Math.round(ageHours) === 1 ? 'hour' : 'hours'} old`}. A successful refresh replaces {user ? 'your saved copy' : 'the shared guest copy'}; your thesis stays unchanged.</p>}
      {(result.warnings || []).map((warning, i) => <p key={i} role="status" className="border border-accent/40 bg-accent/5 p-3 text-sm text-accent">{warning}</p>)}
      {result.cache_warning && <p role="status" className="p-3 text-sm text-accent">{result.cache_warning} Keep this page open or rerun to save your research.</p>}
      {/* Terminal Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between border-b border-border-base pb-4">
        <div>
          <div className="flex flex-wrap items-center gap-4 mb-2">
            <h2 className="text-4xl font-mono font-bold tracking-tight text-txt-primary">{result.ticker}</h2>
            <div className="flex items-center gap-2 border border-accent/30 bg-accent/5 px-2 py-1 rounded-sm">
              <span className="h-1.5 w-1.5 bg-accent rounded-sm animate-pulse" />
              <span className="text-micro font-mono font-medium uppercase tracking-widest text-accent">
                AI research
              </span>
            </div>
          </div>
          <p className="text-sm font-mono text-txt-muted uppercase tracking-widest">
            Updated: {new Date(result.timestamp).toLocaleDateString()} // {new Date(result.timestamp).toLocaleTimeString()}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
        <Button variant="outline" size="sm" disabled={isThesisLoading || !!thesisError} onClick={() => setShowThesisEditor(true)}>
          {existingThesis ? 'Edit thesis' : 'Save thesis'}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="gap-2 font-mono text-micro tracking-widest uppercase border border-border-base bg-surface-1 text-txt-secondary hover:text-txt-primary hover:bg-surface-2 hover:border-border-strong rounded-sm h-8"
        >
          <RefreshCw className={cn("h-3 w-3", isRefreshing && "animate-spin")} />
          <span>Refresh analysis</span>
        </Button>
        </div>
      </div>

      <p className="text-sm text-txt-secondary">AI research · Model confidence is not a forecast. Verify the evidence before investing.</p>

      {thesisError && <p role="alert" className="text-sm text-bear">Unable to check your saved thesis. Please refresh or sign in again.</p>}
      <ThesisEditor isOpen={showThesisEditor} onClose={() => setShowThesisEditor(false)} ticker={result.ticker} existingThesis={existingThesis} analysis={result} />
      {/* Raw Segmented Control */}
      <div className="flex flex-wrap w-full border-b border-border-base/50 gap-2 pb-3">
        {tabs.map((tab) => {
           // Disable fundamentals tab if no data
           if (tab.id === 'fundamentals' && !Object.values(result.fundamental_data || {}).some(value => value && typeof value === 'object' && !Array.isArray(value) && Object.values(value).some(item => item != null))) return null;

           const isActive = activeTab === tab.id;
           return (
             <button
               key={tab.id}
               aria-pressed={isActive}
               onClick={() => setActiveTab(tab.id)}
               className={cn(
                 "flex min-h-11 items-center justify-center gap-2 px-4 py-2 font-mono text-micro tracking-wide transition-colors rounded-sm border",
                 isActive 
                   ? "text-txt-primary bg-surface-2 border-border-strong" 
                   : "text-txt-muted hover:text-txt-secondary bg-surface-1 border-border-base hover:bg-surface-2"
               )}
             >
               <tab.icon className={cn("h-3 w-3", isActive ? "text-accent" : "text-txt-muted")} />
               {tab.label}
             </button>
           );
        })}
      </div>

      {/* Content Area (No Animation) */}
      <div className="min-h-[400px]">
        {activeTab === 'thesis' && (
          <div className="grid gap-6 xl:grid-cols-3">
            {/* Main Thesis Content */}
            <div className="xl:col-span-2 space-y-6">
              
              <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
                <div className="border-b border-border-base/50 bg-surface-2 px-4 py-2 flex items-center gap-2">
                    <FileText className="h-3 w-3 text-txt-muted" />
                    <h3 className="font-mono text-micro font-bold uppercase tracking-widest text-txt-primary">Research summary</h3>
                </div>
                <div className="p-5 sm:p-7 bg-canvas">
                  <div className="research-markdown research-copy max-w-[75ch] text-txt-secondary">
                    <ReactMarkdown skipHtml>{result.summary}</ReactMarkdown>
                  </div>
                </div>
              </div>

              {/* Reasoning Steps */}
              <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
                <div className="border-b border-border-base/50 bg-surface-2 px-4 py-2 flex flex-wrap justify-between items-center gap-2">
                  <h3 className="font-mono text-micro font-bold uppercase tracking-widest text-txt-primary">Analysis activity</h3>
                  <span className="font-mono text-micro text-txt-muted uppercase tracking-wider">{(result.reasoning_steps || []).length} steps</span>
                </div>
                <div className="p-5 sm:p-6 bg-canvas">
                  <ul className="space-y-4 max-w-[75ch]">
                    {(result.reasoning_steps || []).map((step, i) => (
                      <li key={i} className="flex gap-3 text-sm">
                        <div className="flex shrink-0 w-6 h-full font-mono text-micro text-txt-muted font-bold pt-1">
                          [{i + 1}]
                        </div>
                        <p className="research-copy text-txt-secondary">{step}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Sidebar: Sentiment & Quick Stats */}
            <div className="min-w-0 space-y-6">
              <SentimentCard 
                 data={result}
              />
              
              {/* Tools Used Pill */}
              <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
                <div className="border-b border-border-base/50 bg-surface-2 px-4 py-2">
                  <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-txt-primary">Data & analysis tools</h4>
                </div>
                <div className="p-3 bg-canvas flex flex-col gap-1.5">
                  {(result.tools_used || []).map((tool) => (
                    <div key={tool} className="flex items-center gap-2 px-2 py-1.5 border border-border-base/50 bg-surface-2 rounded-[2px]">
                      <span className="text-micro font-mono text-txt-secondary uppercase tracking-widest">{({fetch_news_headlines: 'News retrieval', fetch_price_data: 'Historical prices', analyze_sentiment: 'Sentiment assessment', generate_skeptic_critique: 'Independent review'} as Record<string, string>)[tool] || tool.replace(/_/g, ' ')}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'news' && (
          <section className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
            <div className="border-b border-border-base px-5 py-5 sm:px-7">
              <div className="flex flex-wrap items-baseline justify-between gap-2"><h3 className="text-lg text-txt-primary">News used in this analysis</h3><span className="font-mono text-micro uppercase tracking-widest text-txt-muted">{(result.headlines || []).length} headlines</span></div>
              <p className="mt-2 max-w-[75ch] text-sm leading-relaxed text-txt-secondary">Headlines are provided by the news feed. They are evidence inputs, not independently verified facts.</p>
            </div>
            {(result.headlines || []).length === 0 ? <p className="p-6 text-sm text-txt-secondary">No headlines were saved for this analysis.</p> : <ul className="divide-y divide-border-base list-none">{(result.headlines || []).map((headline, i) => {
              const assessment = result.headline_analyses?.find(item => item.headline === headline);
              const sourceUrl = safeSourceUrl(assessment?.url);
              const published = assessment?.published_at && !Number.isNaN(Date.parse(assessment.published_at)) ? new Date(assessment.published_at).toLocaleDateString() : null;
              return <li key={i}><details className="news-disclosure group">
                <summary className="flex cursor-pointer items-start gap-4 px-5 py-4 sm:px-7 hover:bg-surface-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-[-2px]"><span className="font-mono text-micro text-accent pt-1 shrink-0">{String(i + 1).padStart(2, '0')}</span><span className="research-copy min-w-0 flex-1 text-txt-primary">{headline}</span><span aria-hidden="true" className="news-chevron font-mono text-lg text-txt-muted shrink-0">+</span></summary>
                <div className="mx-5 mb-5 ml-12 border-l-2 border-accent/30 pl-4 sm:mx-7 sm:ml-14 max-w-[75ch] research-copy text-txt-secondary">{assessment ? <><p className="font-mono text-micro uppercase tracking-wide text-accent">{assessment.sentiment} · {Math.round(assessment.confidence * 100)}% model confidence</p><p className="mt-2">{assessment.reasoning}</p>{assessment.key_entities?.length > 0 && <p className="mt-3 text-sm text-txt-muted">Entities: {assessment.key_entities.join(', ')}</p>}{(assessment.source || published) && <p className="mt-2 text-sm text-txt-muted">{[assessment.source, published].filter(Boolean).join(' · ')}</p>}{sourceUrl && <a href={sourceUrl} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block text-sm text-accent underline underline-offset-4">Read source article <span className="sr-only">(opens in a new tab)</span></a>}</> : <p>No individual headline assessment was saved for this snapshot.</p>}</div>
              </details></li>;
            })}</ul>}
          </section>
        )}

        {activeTab === 'prices' && (
          <Suspense fallback={<div className="border border-border-base bg-surface-1 p-8 font-mono text-sm text-txt-muted" role="status">Loading price chart…</div>}><PriceChart key={result.ticker} points={result.price_data || []} ticker={result.ticker} currency={result.fundamental_data?.info?.currency ?? undefined} /></Suspense>
        )}

        {activeTab === 'skeptic' && (
          <SkepticCard data={result} />
        )}

        <div hidden={activeTab !== 'debate'}>
          <DebatePanel key={result.ticker} ticker={result.ticker} />
        </div>

        {activeTab === 'fundamentals' && result.fundamental_data && (
          <FundamentalsCard data={result.fundamental_data} />
        )}
      </div>
    </div>
  );
};

export default ResultsTabs;
