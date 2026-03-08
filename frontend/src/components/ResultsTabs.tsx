import { useState } from 'react';
import { RefreshCw, FileText, BarChart3, ShieldAlert } from 'lucide-react';
import { Button } from './ui/button';
import FundamentalsCard from './FundamentalsCard';
import SkepticCard from './SkepticCard';
import SentimentCard from './SentimentCard';
import type { AnalysisData } from '../types/api';
import { cn } from '../utils/cn';

interface ResultsTabsProps {
  result: AnalysisData;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const tabs = [
  { id: 'thesis', label: 'INVESTMENT_THESIS', icon: FileText },
  { id: 'skeptic', label: 'BEAR_CASE_RISKS', icon: ShieldAlert },
  { id: 'fundamentals', label: 'FUNDAMENTAL_DATA', icon: BarChart3 },
];

const ResultsTabs = ({ result, onRefresh, isRefreshing }: ResultsTabsProps) => {
  const [activeTab, setActiveTab] = useState('thesis');

  // Helper to safely render markdown paragraphs as stark terminal lines
  const renderMarkdown = (text: string) => {
    return text.split('\n\n').map((paragraph, idx) => (
      <p key={idx} className="mb-4 font-mono text-micro leading-relaxed text-txt-secondary last:mb-0 uppercase tracking-wide">
        {'> '} {paragraph}
      </p>
    ));
  };

  return (
    <div className="space-y-6">
      {/* Terminal Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between border-b border-border-base pb-4">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h2 className="text-4xl font-mono font-bold tracking-tight text-txt-primary">{result.ticker}</h2>
            <div className="flex items-center gap-2 border border-accent/30 bg-accent/5 px-2 py-1 rounded-sm">
              <span className="h-1.5 w-1.5 bg-accent rounded-sm animate-pulse" />
              <span className="text-micro font-mono font-medium uppercase tracking-widest text-accent">
                {result.agent_type}_ANALYSIS
              </span>
            </div>
          </div>
          <p className="text-sm font-mono text-txt-muted uppercase tracking-widest">
            LOG_ENTRY: {new Date(result.timestamp).toLocaleDateString()} // {new Date(result.timestamp).toLocaleTimeString()}
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onRefresh}
          disabled={isRefreshing}
          className="gap-2 font-mono text-micro tracking-widest uppercase border border-border-base bg-surface-1 text-txt-secondary hover:text-txt-primary hover:bg-surface-2 hover:border-border-strong rounded-sm h-8"
        >
          <RefreshCw className={cn("h-3 w-3", isRefreshing && "animate-spin")} />
          <span>RERUN_SEQ</span>
        </Button>
      </div>

      {/* Raw Segmented Control */}
      <div className="flex w-full border-b border-border-base/50 gap-1 overflow-x-auto no-scrollbar pb-1">
        {tabs.map((tab) => {
           // Disable fundamentals tab if no data
           if (tab.id === 'fundamentals' && !result.fundamental_data) return null;

           const isActive = activeTab === tab.id;
           return (
             <button
               key={tab.id}
               onClick={() => setActiveTab(tab.id)}
               className={cn(
                 "flex items-center gap-2 px-4 py-2 font-mono text-micro tracking-widest transition-colors outline-none rounded-sm border shrink-0 uppercase",
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
          <div className="grid gap-6 md:grid-cols-3">
            {/* Main Thesis Content */}
            <div className="md:col-span-2 space-y-6">
              
              <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
                <div className="border-b border-border-base/50 bg-surface-2 px-4 py-2 flex items-center gap-2">
                    <FileText className="h-3 w-3 text-txt-muted" />
                    <h3 className="font-mono text-micro font-bold uppercase tracking-widest text-txt-primary">EXECUTIVE_SUMMARY</h3>
                </div>
                <div className="p-5 bg-canvas">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    {renderMarkdown(result.summary)}
                  </div>
                </div>
              </div>

              {/* Reasoning Steps */}
              <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
                <div className="border-b border-border-base/50 bg-surface-2 px-4 py-2 flex justify-between items-center">
                  <h3 className="font-mono text-micro font-bold uppercase tracking-widest text-txt-primary">METHODOLOGY</h3>
                  <span className="font-mono text-micro text-txt-muted uppercase tracking-widest">STEPS_TAKEN: {result.reasoning_steps.length}</span>
                </div>
                <div className="p-4 bg-canvas">
                  <ul className="space-y-2 font-mono">
                    {result.reasoning_steps.map((step, i) => (
                      <li key={i} className="flex gap-3 text-micro tracking-widest uppercase">
                        <div className="flex shrink-0 w-6 h-full text-txt-muted font-bold">
                          [{i + 1}]
                        </div>
                        <p className="text-txt-secondary leading-relaxed">{step}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {/* Sidebar: Sentiment & Quick Stats */}
            <div className="space-y-6">
              <SentimentCard 
                 data={result}
              />
              
              {/* Tools Used Pill */}
              <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
                <div className="border-b border-border-base/50 bg-surface-2 px-4 py-2">
                  <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-txt-primary">TOOLS_DEPLOYED</h4>
                </div>
                <div className="p-3 bg-canvas flex flex-col gap-1.5">
                  {result.tools_used.map((tool) => (
                    <div key={tool} className="flex items-center gap-2 px-2 py-1.5 border border-border-base/50 bg-surface-2 rounded-[2px]">
                      <span className="text-micro font-mono text-txt-secondary uppercase tracking-widest">{`>`} {tool}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'skeptic' && (
          <SkepticCard data={result} />
        )}

        {activeTab === 'fundamentals' && result.fundamental_data && (
          <FundamentalsCard data={result.fundamental_data} />
        )}
      </div>
    </div>
  );
};

export default ResultsTabs;
