/**
 * ThesisComparisonBanner - Show analysis changes since thesis creation
 * Stage 4: Analysis-Thesis Linkage
 */

import { TrendingUp, TrendingDown, ArrowRight, RefreshCw } from 'lucide-react';
import { motion } from 'framer-motion';
import type { ThesisComparison } from '../types/thesis';

interface ThesisComparisonBannerProps {
  comparison: ThesisComparison | null;
  onRefresh?: () => void;
}

export default function ThesisComparisonBanner({ 
  comparison, 
  onRefresh 
}: ThesisComparisonBannerProps) {
  if (!comparison || !comparison.has_comparison || !comparison.changes?.length) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -5 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-primary/30 bg-primary/5 p-4"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold text-foreground">
          Analysis Changed Since Your Thesis
        </h4>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1 rounded hover:bg-muted/50 transition-colors"
            title="Re-run analysis"
          >
            <RefreshCw className="h-4 w-4 text-muted-foreground" />
          </button>
        )}
      </div>

      {/* Changes */}
      <div className="space-y-2">
        {comparison.changes?.map((change, index) => (
          <div 
            key={index} 
            className="flex items-center gap-2 text-sm"
          >
            {change.direction === 'increased' ? (
              <TrendingUp className="h-4 w-4 text-success shrink-0" />
            ) : change.direction === 'decreased' ? (
              <TrendingDown className="h-4 w-4 text-destructive shrink-0" />
            ) : (
              <ArrowRight className="h-4 w-4 text-warning shrink-0" />
            )}
            
            <span className="text-muted-foreground capitalize">
              {change.field}:
            </span>
            
            <span className="text-foreground/70">
              {typeof change.from === 'number' 
                ? `${Math.round(change.from * 100)}%`
                : change.from}
            </span>
            
            <ArrowRight className="h-3 w-3 text-muted-foreground shrink-0" />
            
            <span className={
              change.direction === 'increased' 
                ? 'text-success font-medium'
                : change.direction === 'decreased'
                  ? 'text-destructive font-medium'
                  : 'text-warning font-medium'
            }>
              {typeof change.to === 'number' 
                ? `${Math.round(change.to * 100)}%`
                : change.to}
            </span>
            
            {change.delta && (
              <span className={`text-xs ${
                change.delta > 0 ? 'text-success' : 'text-destructive'
              }`}>
                ({change.delta > 0 ? '+' : ''}{Math.round(change.delta * 100)}%)
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      {comparison.change_summary && (
        <p className="text-xs text-muted-foreground mt-3 pt-2 border-t border-border">
          {comparison.change_summary}
        </p>
      )}
    </motion.div>
  );
}
