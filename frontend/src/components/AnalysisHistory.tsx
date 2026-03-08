import { RefreshCw, Trash2, Clock, Terminal } from 'lucide-react';
import { ListSkeleton } from './ui/skeleton';
import { useCachedTickers, useDeleteAnalysis } from '../api/hooks';
import type { CachedTickerItem } from '../types/api';

interface AnalysisHistoryProps {
  onSelectHistory: (ticker: string) => void;
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

const AnalysisHistory = ({ onSelectHistory }: AnalysisHistoryProps) => {
  const { data, isLoading, refetch } = useCachedTickers();
  const deleteMutation = useDeleteAnalysis();
  
  // Handle case where item might be just a string from old cache
  const rawTickers = data?.tickers || [];
  const tickers: CachedTickerItem[] = rawTickers.map((item: string | CachedTickerItem) => {
    if (typeof item === 'string') {
      return { symbol: item, timestamp: null };
    }
    return item;
  });

  const handleDelete = (e: React.MouseEvent, symbol: string) => {
    e.stopPropagation();
    deleteMutation.mutate(symbol, {
      onSuccess: () => refetch(),
    });
  };

  return (
    <div className="flex flex-col h-full border border-border-base bg-surface-1 rounded-sm overflow-hidden">
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-border-base bg-surface-2/30">
        <div className="flex items-center gap-2 text-txt-secondary">
          <Terminal className="h-3 w-3" />
          <span className="text-micro font-mono uppercase tracking-widest text-txt-muted">CACHE_LOG</span>
        </div>
        <button 
          className="p-1 text-txt-muted hover:text-txt-primary hover:bg-surface-2 transition-colors rounded-sm outline-none" 
          onClick={() => refetch()}
          title="REFRESH_CACHE"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      <div className="p-2 flex-1 overflow-y-auto no-scrollbar">
        {isLoading ? (
           <div className="space-y-2 p-2">
              <ListSkeleton items={4} />
           </div>
        ) : tickers.length === 0 ? (
           <div className="flex flex-col items-center justify-center py-12 text-center h-full">
              <Clock className="mb-3 h-4 w-4 text-txt-muted/30" />
              <p className="text-micro font-mono tracking-widest text-txt-muted uppercase">CACHE_EMPTY</p>
           </div>
        ) : (
          <div className="flex flex-col gap-1">
            {tickers.map((item) => (
              <div
                key={item.symbol}
                className="group relative flex items-center justify-between bg-surface-2 border border-border-base/50 hover:border-border-strong hover:bg-surface-3 p-2 transition-colors cursor-pointer rounded-sm"
                onClick={() => onSelectHistory(item.symbol)}
                title={formatFullDateTime(item.timestamp)}
              >
                <div className="flex items-center justify-between w-full">
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-micro font-bold tracking-widest text-txt-primary">
                      {item.symbol}
                    </span>
                    <span className="font-mono text-micro tracking-widest text-txt-muted uppercase">
                      {formatRelativeTime(item.timestamp)}
                    </span>
                  </div>
                  
                  <button
                    className="opacity-0 group-hover:opacity-100 p-1 text-txt-muted hover:bg-kill hover:text-canvas transition-all rounded-sm"
                    onClick={(e) => handleDelete(e, item.symbol)}
                    disabled={deleteMutation.isPending}
                    title="PURGE_RECORD"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisHistory;