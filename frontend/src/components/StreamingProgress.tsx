/**
 * StreamingProgress - Real-time progress display for streaming analysis
 * Stage 4: Shows tool completion status as analysis progresses
 */

import { CheckCircle, Circle, Loader2, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import type { StreamEvent } from '../hooks/useStreamingAnalysis';

interface Tool {
  name: string;
  label: string;
  icon: string;
}

const TOOLS: Tool[] = [
  { name: 'fetch_news_headlines', label: 'Fetching News', icon: '📰' },
  { name: 'fetch_price_data', label: 'Getting Prices', icon: '📈' },
  { name: 'analyze_sentiment', label: 'Analyzing Sentiment', icon: '🧠' },
  { name: 'generate_skeptic_critique', label: 'Skeptic Review', icon: '🔍' },
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
    <div className="rounded-lg border border-border bg-card p-4 space-y-4">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            {isStreaming ? 'Analyzing...' : error ? 'Failed' : 'Complete'}
          </span>
          <span className="font-medium">{Math.round(progress * 100)}%</span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <motion.div
            className={`h-full ${error ? 'bg-destructive' : 'bg-primary'}`}
            initial={{ width: 0 }}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          />
        </div>
      </div>

      {/* Tool progress */}
      <div className="space-y-2">
        {TOOLS.map((tool) => {
          const status = getToolStatus(tool.name);
          const message = getToolMessage(tool.name);

          return (
            <motion.div
              key={tool.name}
              className={`flex items-center gap-3 p-2 rounded-md transition-colors ${
                status === 'active' 
                  ? 'bg-primary/10' 
                  : status === 'completed'
                    ? 'bg-success/5'
                    : 'bg-transparent'
              }`}
              initial={{ opacity: 0.5 }}
              animate={{ opacity: status === 'pending' ? 0.5 : 1 }}
            >
              {/* Icon */}
              <span className="text-lg">{tool.icon}</span>

              {/* Status indicator */}
              {status === 'completed' ? (
                <CheckCircle className="h-4 w-4 text-success shrink-0" />
              ) : status === 'active' ? (
                <Loader2 className="h-4 w-4 text-primary animate-spin shrink-0" />
              ) : (
                <Circle className="h-4 w-4 text-muted-foreground shrink-0" />
              )}

              {/* Label and message */}
              <div className="flex-1 min-w-0">
                <span className={`text-sm ${
                  status === 'active' ? 'font-medium text-foreground' : 'text-muted-foreground'
                }`}>
                  {tool.label}
                </span>
                {message && status === 'completed' && (
                  <p className="text-xs text-muted-foreground truncate">
                    {message}
                  </p>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 p-2 rounded bg-destructive/10 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}
