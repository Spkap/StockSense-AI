/**
 * ThesisComparisonBanner - Show analysis changes since thesis creation
 * Stage 4: Analysis-Thesis Linkage
 * 
 * Obsidian Terminal styled — monochrome, dense, mechanical.
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
      className="border border-accent/30 bg-accent/5 rounded-sm overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-accent/20 bg-accent/5">
        <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-txt-primary">
          DELTA_SINCE_THESIS
        </h4>
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="p-1 rounded-sm hover:bg-surface-2 transition-colors"
            title="Re-run analysis"
          >
            <RefreshCw className="h-3.5 w-3.5 text-txt-muted" />
          </button>
        )}
      </div>

      {/* Changes */}
      <div className="p-3 space-y-1.5 bg-canvas">
        {comparison.changes?.map((change, index) => (
          <div 
            key={index} 
            className="flex items-center gap-2 text-micro font-mono uppercase tracking-wider"
          >
            {change.direction === 'increased' ? (
              <TrendingUp className="h-3.5 w-3.5 text-bull shrink-0" />
            ) : change.direction === 'decreased' ? (
              <TrendingDown className="h-3.5 w-3.5 text-bear shrink-0" />
            ) : (
              <ArrowRight className="h-3.5 w-3.5 text-accent shrink-0" />
            )}
            
            <span className="text-txt-muted">
              {change.field}:
            </span>
            
            <span className="text-txt-secondary">
              {typeof change.from === 'number' 
                ? `${Math.round(change.from * 100)}%`
                : change.from}
            </span>
            
            <ArrowRight className="h-3 w-3 text-txt-muted/50 shrink-0" />
            
            <span className={
              change.direction === 'increased' 
                ? 'text-bull font-bold'
                : change.direction === 'decreased'
                  ? 'text-bear font-bold'
                  : 'text-accent font-bold'
            }>
              {typeof change.to === 'number' 
                ? `${Math.round(change.to * 100)}%`
                : change.to}
            </span>
            
            {change.delta && (
              <span className={`${
                change.delta > 0 ? 'text-bull' : 'text-bear'
              } font-bold`}>
                ({change.delta > 0 ? '+' : ''}{Math.round(change.delta * 100)}%)
              </span>
            )}
          </div>
        ))}
      </div>

      {/* Summary */}
      {comparison.change_summary && (
        <p className="text-micro font-mono text-txt-muted uppercase tracking-wider px-4 py-2 border-t border-border-base/50 bg-surface-1">
          {comparison.change_summary}
        </p>
      )}
    </motion.div>
  );
}
