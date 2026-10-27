import { useState } from 'react';
import { RefreshCw, Clock, Terminal, Trash2 } from 'lucide-react';
import { ListSkeleton } from './ui/skeleton';
import { useCachedTickers, useDeleteAnalysis } from '../api/hooks';
import { useAuth } from '../context/AuthContext';
import type { CachedTickerItem } from '../types/api';

interface AnalysisHistoryProps {
  onSelectHistory: (ticker: string) => void;
  onRemoved: (ticker: string) => void;
}

function formatRelativeTime(timestamp: string | null): string {
  if (!timestamp) return 'UNKNOWN';
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'JUST_NOW';
    if (diffMins < 60) return `${diffMins}M_AGO`;
    if (diffHours < 24) return `${diffHours}H_AGO`;
    if (diffDays === 1) return 'YESTERDAY';
    if (diffDays < 7) return `${diffDays}D_AGO`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }).replace(' ', '_').toUpperCase();
  } catch {
    return 'UNKNOWN';
  }
}

function formatFullDateTime(timestamp: string | null): string {
  if (!timestamp) return 'UNKNOWN_DATE';
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    }).toUpperCase();
  } catch {
    return 'UNKNOWN_DATE';
  }
}

const AnalysisHistory = ({ onSelectHistory, onRemoved }: AnalysisHistoryProps) => {
  const { data, isLoading, isError, refetch } = useCachedTickers();
  const { user } = useAuth();
  const remove = useDeleteAnalysis();
  const [confirmTicker, setConfirmTicker] = useState<string | null>(null);
  
  // Handle case where item might be just a string from old cache
  const rawTickers = data?.tickers || [];
  const tickers: CachedTickerItem[] = rawTickers.map((item: string | CachedTickerItem) => {
    if (typeof item === 'string') {
      return { symbol: item, timestamp: null };
    }
    return item;
  });

  return (
    <div className="flex flex-col h-full border border-border-base bg-surface-1 rounded-sm overflow-hidden">
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border-base bg-surface-2/30">
        <div className="flex items-center gap-2 text-txt-secondary">
          <Terminal className="h-3 w-3" />
          <span className="text-micro font-mono uppercase tracking-widest text-txt-muted">{user ? 'My saved research' : 'Shared guest research'}</span>
        </div>
        <button 
          className="p-1 text-txt-muted hover:text-txt-primary hover:bg-surface-2 transition-colors rounded-sm outline-none" 
          onClick={() => refetch()}
          title="Refresh saved research"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      <div className="p-2 flex-1 overflow-y-auto no-scrollbar">
        {isLoading ? (
           <div className="space-y-2 p-2">
              <ListSkeleton items={4} />
           </div>
        ) : isError ? (
          <p role="alert" className="p-3 text-sm text-bear">Could not load saved research. Try refreshing.</p>
        ) : tickers.length === 0 ? (
           <div className="flex flex-col items-center justify-center py-12 text-center h-full">
              <Clock className="mb-3 h-4 w-4 text-txt-muted/30" />
              <p className="text-micro font-mono tracking-widest text-txt-muted uppercase">No saved research yet</p>
           </div>
        ) : (
          <div className="flex flex-col gap-1">
            {tickers.map((item) => (
              <div key={item.symbol} className="group flex items-center bg-surface-2 border border-border-base/50 hover:border-border-strong hover:bg-surface-3 rounded-sm">
                <button type="button" aria-label={`Open saved research for ${item.symbol}`} onClick={() => onSelectHistory(item.symbol)} title={formatFullDateTime(item.timestamp)} className="flex min-w-0 flex-1 items-center gap-3 p-2 text-left">
                    <span className="font-mono text-micro font-bold tracking-widest text-txt-primary">
                      {item.symbol}
                    </span>
                    <span className="font-mono text-micro tracking-widest text-txt-muted uppercase">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                </button>
                <button type="button" aria-label={`Remove saved research for ${item.symbol}`} className="p-2 text-txt-muted hover:text-kill" onClick={() => { remove.reset(); setConfirmTicker(item.symbol); }}><Trash2 className="h-3.5 w-3.5" /></button>
              </div>
            ))}
          </div>
        )}
      </div>
      {confirmTicker && <div role="dialog" aria-label="Remove saved research" className="border-t border-border-base p-3 text-sm text-txt-secondary">
        <p>Remove {confirmTicker} research and its saved debate? {user ? 'This removes only your copy.' : 'This removes the shared guest copy for all guests.'} Theses are not deleted.</p>
        {remove.isError && <p role="alert" className="mt-2 text-bear">Could not remove research. Please try again.</p>}
        <div className="mt-3 flex gap-4"><button type="button" disabled={remove.isPending} className="text-kill underline" onClick={async () => { try { await remove.mutateAsync(confirmTicker); onRemoved(confirmTicker); setConfirmTicker(null); } catch { /* mutation displays its error */ } }}>Remove research</button><button type="button" className="text-txt-secondary underline" onClick={() => { remove.reset(); setConfirmTicker(null); }}>Cancel</button></div>
      </div>}
    </div>
  );
};

export default AnalysisHistory;
