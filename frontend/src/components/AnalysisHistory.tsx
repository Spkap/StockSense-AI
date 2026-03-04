import { History, RefreshCw, Trash2, Clock } from 'lucide-react';
import { Button } from './ui/button';
import { ListSkeleton } from './ui/skeleton';
import { useCachedTickers, useDeleteAnalysis } from '../api/hooks';
import type { CachedTickerItem } from '../types/api';


interface AnalysisHistoryProps {
  onSelectHistory: (ticker: string) => void;
}

function formatRelativeTime(timestamp: string | null): string {
  if (!timestamp) return 'Unknown';
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return 'Unknown';
  }
}

function formatFullDateTime(timestamp: string | null): string {
  if (!timestamp) return 'Unknown date';
  try {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Unknown date';
  }
}

const AnalysisHistory = ({ onSelectHistory }: AnalysisHistoryProps) => {
  const { data, isLoading, refetch } = useCachedTickers();
  const deleteMutation = useDeleteAnalysis();
  
  const tickers: CachedTickerItem[] = (data?.tickers || []).map((item: string | CachedTickerItem) => {
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
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2 text-muted-foreground">
          <History className="h-4 w-4" />
          <span className="text-sm font-medium">Recent Activity</span>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-6 w-6 text-muted-foreground hover:text-foreground" 
          onClick={() => refetch()}
          title="Refresh history"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </div>

      {isLoading ? (
         <div className="space-y-4">
            <ListSkeleton items={3} />
         </div>
      ) : tickers.length === 0 ? (
         <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/50 py-12 text-center">
            <Clock className="mb-2 h-8 w-8 text-muted-foreground/30" />
            <p className="text-sm text-muted-foreground">No recent analyses</p>
         </div>
      ) : (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-1">
          {tickers.map((item) => (
            <div
              key={item.symbol}
              className="group relative flex items-center justify-between rounded-xl bg-background/50 border border-border/40 p-3 transition-all duration-300 hover:border-primary/20 hover:bg-background hover:shadow-md"
            >
              <button
                onClick={() => onSelectHistory(item.symbol)}
                className="flex flex-1 items-center gap-3 text-left"
                title={formatFullDateTime(item.timestamp)}
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary text-xs font-bold text-foreground transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  {item.symbol.substring(0, 2)}
                </div>
                <div className="flex flex-col">
                  <span className="font-semibold text-sm text-foreground">
                    {item.symbol}
                  </span>
                  <span className="text-xs text-muted-foreground group-hover:text-muted-foreground/80">
                    {formatRelativeTime(item.timestamp)}
                  </span>
                </div>
              </button>
              
              <Button
                variant="ghost"
                size="icon"
                className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 bg-background/80 backdrop-blur-sm transition-opacity group-hover:opacity-100 hover:bg-destructive/10 hover:text-destructive"
                onClick={(e) => handleDelete(e, item.symbol)}
                disabled={deleteMutation.isPending}
                title={`Delete analysis for ${item.symbol}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnalysisHistory;