/**
 * StreamingProgress - Real-time progress display for streaming analysis
 * Stage 4: Shows tool completion status as analysis progresses
 * 
 * Obsidian Terminal styled — monochrome, dense, mechanical.
 */

import { motion } from 'framer-motion';
import { cn } from '../utils/cn';
import type { StreamEvent } from '../hooks/useStreamingAnalysis';

interface Tool {
  name: string;
  label: string;
}

const TOOLS: Tool[] = [
  { name: 'fetch_news_headlines', label: 'FETCH_NEWS' },
  { name: 'fetch_price_data', label: 'FETCH_PRICE' },
  { name: 'analyze_sentiment', label: 'AI_SENTIMENT' },
  { name: 'generate_skeptic_critique', label: 'SKEPTIC_REVIEW' },
];

interface StreamingProgressProps {
  isStreaming: boolean;
  progress: number;
  currentTool: string | null;
  events: StreamEvent[];
  error: string | null;
}

export default function StreamingProgress({
  isStreaming,
  progress,
  currentTool,
  events,
  error,
}: StreamingProgressProps) {
  // Get completed tools from events
  const completedTools = new Set(
    events
      .filter(e => e.type === 'tool_completed')
      .map(e => e.tool)
  );

  const getToolStatus = (toolName: string) => {
    if (completedTools.has(toolName)) return 'completed';
    if (currentTool === toolName) return 'active';
    return 'pending';
  };

  const getToolMessage = (toolName: string) => {
    const event = events.find(
      e => e.type === 'tool_completed' && e.tool === toolName
    );
    return event?.message || '';
  };

  if (!isStreaming && events.length === 0) {
    return null;
  }

  return (
    <div className="border border-border-base bg-surface-1 rounded-sm font-mono overflow-hidden">
      {/* Progress bar */}
      <div className="p-3 border-b border-border-base/50 bg-canvas">
        <div className="flex justify-between text-micro tracking-widest uppercase font-bold mb-2">
          <span className="text-txt-secondary">
            {isStreaming ? 'PROCESSING' : error ? 'HALTED_ERR' : 'COMPLETE'}
          </span>
          <span className="text-accent">{Math.round(progress * 100)}%</span>
        </div>
        <div className="h-[2px] w-full bg-surface-2 rounded-none overflow-hidden">
          <motion.div
            className={`h-full ${error ? 'bg-kill' : 'bg-accent'}`}
            initial={{ width: 0 }}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Tool progress */}
      <div className="flex flex-col gap-1 p-3 bg-canvas">
        {TOOLS.map((tool) => {
          const status = getToolStatus(tool.name);
          const message = getToolMessage(tool.name);

          return (
            <motion.div
              key={tool.name}
              className={cn(
                "flex items-center gap-3 px-3 py-2 transition-colors duration-100 border rounded-sm",
                status === 'active' 
                  ? 'bg-surface-2 border-border-strong' 
                  : status === 'completed'
                    ? 'bg-surface-1 border-border-base/50'
                    : 'bg-surface-1 border-border-base/30'
              )}
              initial={{ opacity: 0.5 }}
              animate={{ opacity: status === 'pending' ? 0.5 : 1 }}
            >
              {/* Status indicator */}
              <div className="flex h-5 w-5 shrink-0 items-center justify-center font-bold text-micro">
                {status === 'completed' ? (
                  <span className="text-bull">[X]</span>
                ) : status === 'active' ? (
                  <span className="text-accent animate-pulse text-sm">{'>'}</span>
                ) : (
                  <span className="text-txt-muted/50">[ ]</span>
                )}
              </div>

              {/* Label and message */}
              <div className="flex-1 min-w-0 flex items-center justify-between">
                <div className="flex flex-col">
                  <span className={cn(
                    "text-micro tracking-widest uppercase font-bold",
                    status === 'active' ? 'text-txt-primary' : 
                    status === 'completed' ? 'text-txt-secondary' : 'text-txt-muted'
                  )}>
                    {tool.label}
                  </span>
                  {message && status === 'completed' && (
                    <span className="text-micro text-txt-muted truncate mt-0.5 tracking-wider uppercase">
                      {message}
                    </span>
                  )}
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

      {/* Error display */}
      {error && (
        <div className="border-t border-kill bg-kill/10 p-3 text-micro font-bold tracking-widest text-kill uppercase">
          ERR: {error}
        </div>
      )}
    </div>
  );
}
