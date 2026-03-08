/**
 * StreamingAnalysisProgress - Real-time streaming analysis view
 * 
 * Replaces the fake progress simulation with actual SSE streaming data.
 * Shows beautiful, animated progress as each agent tool completes.
 */

import { X, TrendingUp, Newspaper, Brain, Search, Terminal } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import { cn } from '../utils/cn';
import type { StreamEvent } from '../hooks/useStreamingAnalysis';

interface StreamingAnalysisProgressProps {
  ticker: string;
  isStreaming: boolean;
  progress: number;
  currentTool: string | null;
  events: StreamEvent[];
  partialData: Partial<{
    headlines: string[];
    price_data: unknown[];
    overall_sentiment: string;
    overall_confidence: number;
    skeptic_sentiment: string;
  }>;
  error: string | null;
  onCancel?: () => void;
}

// Tool configuration with icons and labels
const TOOLS_CONFIG = [
  { 
    name: 'fetch_news_headlines', 
    label: 'FETCH_NEWS', 
    icon: Newspaper,
  },
  { 
    name: 'fetch_price_data', 
    label: 'FETCH_PRICE', 
    icon: TrendingUp,
  },
  { 
    name: 'analyze_sentiment', 
    label: 'AI_SENTIMENT', 
    icon: Brain,
  },
  { 
    name: 'generate_skeptic_critique', 
    label: 'SKEPTIC_REVIEW', 
    icon: Search,
  },
];

export default function StreamingAnalysisProgress({
  ticker,
  isStreaming,
  progress,
  currentTool,
  events,
  partialData,
  error,
  onCancel,
}: StreamingAnalysisProgressProps) {
  // Get completed tools from events
  const completedTools = new Set(
    events
      .filter(e => e.type === 'tool_completed')
      .map(e => e.tool)
  );

  const getToolStatus = (toolName: string): 'pending' | 'active' | 'completed' => {
    if (completedTools.has(toolName)) return 'completed';
    if (currentTool === toolName) return 'active';
    return 'pending';
  };

  const getToolMessage = (toolName: string): string => {
    const event = events.find(
      e => e.type === 'tool_completed' && e.tool === toolName
    );
    return event?.message || '';
  };

  // Get partial insights to show during streaming
  const headlinesCount = partialData.headlines?.length || 0;
  const priceDataPoints = Array.isArray(partialData.price_data) ? partialData.price_data.length : 0;
  const sentiment = partialData.overall_sentiment;

  return (
    <div className="mx-auto w-full max-w-2xl border border-border-base bg-surface-1 font-mono rounded-sm relative overflow-hidden">
      
      <div className="relative z-10 flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border-base bg-surface-2 px-4 py-3">
          <div className="flex items-center gap-3 text-txt-primary">
            <Terminal className="h-4 w-4 text-accent animate-pulse" />
            <h2 className="text-sm font-bold tracking-widest uppercase">
              {ticker} <span className="text-txt-muted font-normal ml-2">// EXEC_SEQUENCE</span>
            </h2>
          </div>
          <span className="text-micro font-bold tracking-widest text-txt-muted uppercase flex items-center gap-2">
            {isStreaming ? (
              <>
               ACTIVE_PROCESS
               <span className="w-1.5 h-3 bg-accent animate-pulse" />
              </>
            ) : error ? 'HALTED_ERR' : 'COMPLETE'}
          </span>
        </div>

        {/* Progress Section */}
        <div className="px-4 py-4 bg-canvas border-b border-border-base/50">
          <div className="mb-2 flex items-center justify-between text-micro tracking-widest font-bold">
            <span className="text-txt-secondary uppercase">PROGRESS_RATIO</span>
            <span className="text-accent">{Math.round(progress * 100)}%</span>
          </div>
          <div className="h-[2px] w-full bg-surface-2 rounded-none overflow-hidden">
            <motion.div 
              className="h-full bg-accent"
              initial={{ width: 0 }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ ease: "linear", duration: 0.3 }}
            />
          </div>
        </div>

        {/* Tool Steps */}
        <div className="flex flex-col gap-1 p-3 bg-canvas">
          {TOOLS_CONFIG.map((tool, index) => {
            const status = getToolStatus(tool.name);
            const message = getToolMessage(tool.name);

            return (
              <motion.div
                key={tool.name}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05, duration: 0.2 }}
                className={cn(
                  "flex items-center gap-4 px-3 py-2 transition-colors duration-100 border rounded-sm",
                  status === 'active' ? "bg-surface-2 border-border-strong" : "bg-surface-1 border-border-base/50"
                )}
              >
                {/* Tool Icon & Status indicator */}
                <div className="flex h-5 w-5 shrink-0 items-center justify-center font-bold text-micro">
                  {status === 'completed' ? (
                    <span className="text-bull">[X]</span>
                  ) : status === 'active' ? (
                     <span className="text-accent animate-pulse text-sm">{'>'}</span>
                  ) : (
                    <span className="text-txt-muted/50">[ ]</span>
                  )}
                </div>

                {/* Tool Info */}
                <div className="flex-1 min-w-0 flex items-center justify-between">
                  <div className="flex flex-col">
                    <span className={cn(
                      "text-micro tracking-widest uppercase font-bold",
                      status === 'active' ? 'text-txt-primary' : 
                      status === 'completed' ? 'text-txt-secondary' : 'text-txt-muted'
                    )}>
                      {tool.label}
                    </span>
                    
                    <AnimatePresence mode="wait">
                      {message && status === 'completed' && (
                        <motion.span
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="text-micro text-txt-muted truncate mt-0.5 tracking-wider uppercase"
                        >
                          {message}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>
                  
                  {/* Status Label */}
                  <span className={cn(
                    "text-micro uppercase tracking-widest text-right font-bold w-12",
                    status === 'completed' ? 'text-bull' : 
                    status === 'active' ? 'text-accent animate-pulse' : 'text-txt-muted/30'
                  )}>
                    {status === 'completed' ? 'OK' : status === 'active' ? 'RUN' : 'WAIT'}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>

        {/* Live Insights Preview */}
        {(headlinesCount > 0 || priceDataPoints > 0 || sentiment) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            className="p-4 border-t border-border-base/50 bg-surface-2/30"
          >
            <div className="mb-3 flex items-center gap-2">
              <div className="h-1.5 w-1.5 bg-accent rounded-sm animate-pulse" />
              <div className="text-micro font-bold uppercase tracking-widest text-txt-secondary">
                LIVE_DATA_FEED
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-2 text-left">
              {headlinesCount > 0 && (
                <div className="border border-border-base/50 bg-surface-1 p-2 rounded-sm border-l-2 border-l-border-strong">
                  <div className="text-micro text-txt-muted uppercase mb-1 tracking-widest font-bold">HEADLINES</div>
                  <div className="text-micro text-txt-primary font-bold">{headlinesCount}</div>
                </div>
              )}
              {priceDataPoints > 0 && (
                <div className="border border-border-base/50 bg-surface-1 p-2 rounded-sm border-l-2 border-l-border-strong">
                  <div className="text-micro text-txt-muted uppercase mb-1 tracking-widest font-bold">DATAPOINTS</div>
                  <div className="text-micro text-txt-primary font-bold">{priceDataPoints}</div>
                </div>
              )}
              {sentiment && (
                <div className="border border-border-base/50 bg-surface-1 p-2 rounded-sm border-l-2 border-l-border-strong">
                  <div className="text-micro text-txt-muted uppercase mb-1 tracking-widest font-bold">SENTIMENT</div>
                  <div className={cn("text-micro uppercase font-bold tracking-wider",
                    sentiment === 'Bullish' ? 'text-bull' :
                    sentiment === 'Bearish' ? 'text-bear' : 'text-txt-secondary'
                  )}>
                    {sentiment}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Error Display */}
        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="border-t border-bear bg-bear/10 p-3 text-micro font-bold tracking-widest text-bear uppercase"
          >
            ERR: {error}
          </motion.div>
        )}

        {/* Cancel Button */}
        {isStreaming && onCancel && (
          <div className="border-t border-border-base p-3 bg-canvas flex justify-end">
            <Button
              variant="ghost"
              onClick={onCancel}
              className="h-8 gap-2 text-micro font-mono tracking-widest uppercase text-txt-muted hover:text-kill hover:bg-kill-dim border border-transparent hover:border-kill/30 rounded-sm"
            >
              <X className="h-3 w-3" />
              ABORT_SEQ
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
