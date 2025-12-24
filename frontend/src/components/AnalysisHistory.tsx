import { History, RefreshCw, Trash2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ListSkeleton } from './ui/skeleton';
import { useCachedTickers, useDeleteAnalysis } from '../api/hooks';
import type { CachedTickerItem } from '../types/api';

interface AnalysisHistoryProps {
  onSelectHistory: (ticker: string) => void;
}

/**
 * Format a timestamp as relative time (e.g., "2 hours ago", "Yesterday")
 */
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
    
    // Format as date for older entries
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return 'Unknown';
  }
}

/**
 * Format a timestamp as full date/time for tooltip
 */
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
  
  // Handle both old (string[]) and new (CachedTickerItem[]) response formats
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
    <Card className="h-full border-border bg-card shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-muted-foreground" />
          <CardTitle className="text-sm font-semibold text-foreground">
            Recent Analyses
          </CardTitle>
        </div>
        <Button 
          variant="ghost" 
          size="icon" 
          className="h-6 w-6" 
          onClick={() => refetch()}
          title="Refresh history"
        >
          <RefreshCw className="h-3 w-3" />
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
           <ListSkeleton items={4} />
        ) : tickers.length === 0 ? (
           <p className="text-center text-sm text-muted-foreground py-4">No recent history</p>
        ) : (
          <div className="space-y-1">
            {tickers.map((item) => (
              <div
                key={item.symbol}
                className="group flex items-center justify-between rounded-md p-2 transition-colors hover:bg-accent"
              >
                <button
                  onClick={() => onSelectHistory(item.symbol)}
                  className="flex flex-col items-start text-left"
                  title={formatFullDateTime(item.timestamp)}
                >
                  <span className="font-semibold text-sm text-foreground group-hover:text-accent-foreground">
                    {item.symbol}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatRelativeTime(item.timestamp)}
                  </span>
                </button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => handleDelete(e, item.symbol)}
                  disabled={deleteMutation.isPending}
                  title={`Delete analysis for ${item.symbol}`}
                >
                  <Trash2 className="h-3 w-3 text-muted-foreground hover:text-destructive" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default AnalysisHistory;