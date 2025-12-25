/**
 * StreamingAnalysisProgress - Real-time streaming analysis view
 * 
 * Replaces the fake progress simulation with actual SSE streaming data.
 * Shows beautiful, animated progress as each agent tool completes.
 */

import { CheckCircle, Loader2, X, Zap, TrendingUp, Newspaper, Brain, Search } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
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
    label: 'Fetching News', 
    icon: Newspaper,
    activeColor: 'text-blue-500',
    bgColor: 'bg-blue-500/10'
  },
  { 
    name: 'fetch_price_data', 
    label: 'Getting Prices', 
    icon: TrendingUp,
    activeColor: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10'
  },
  { 
    name: 'analyze_sentiment', 
    label: 'AI Sentiment Analysis', 
    icon: Brain,
    activeColor: 'text-purple-500',
    bgColor: 'bg-purple-500/10'
  },
  { 
    name: 'generate_skeptic_critique', 
    label: 'Skeptic Review', 
    icon: Search,
    activeColor: 'text-amber-500',
    bgColor: 'bg-amber-500/10'
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
  const confidence = partialData.overall_confidence;

  return (
    <Card className="mx-auto max-w-2xl overflow-hidden border-0 bg-gradient-to-b from-card to-card/80 shadow-xl">
      <CardContent className="p-0">
        {/* Animated Header */}
        <div className="relative overflow-hidden bg-gradient-to-r from-primary/5 via-primary/10 to-primary/5 px-6 py-8 text-center">
          {/* Animated background pulse */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-primary/5 to-transparent"
            animate={{ x: ['-100%', '100%'] }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
          
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="relative"
          >
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/10 ring-4 ring-primary/20">
              <Zap className="h-8 w-8 text-primary" />
            </div>
            
            <h2 className="text-3xl font-bold tracking-tight text-foreground">
              {ticker}
            </h2>
            <p className="mt-1 text-muted-foreground">
              {isStreaming ? 'AI Agent Running...' : error ? 'Analysis Failed' : 'Analysis Complete'}
            </p>
          </motion.div>
        </div>

        {/* Progress Section */}
        <div className="px-6 py-4">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-foreground">Progress</span>
            <span className="font-mono text-muted-foreground">{Math.round(progress * 100)}%</span>
          </div>
          <Progress value={progress * 100} className="h-2" />
        </div>

        {/* Tool Steps */}
        <div className="space-y-1 px-6 pb-4">
          {TOOLS_CONFIG.map((tool, index) => {
            const status = getToolStatus(tool.name);
            const message = getToolMessage(tool.name);
            const Icon = tool.icon;

            return (
              <motion.div
                key={tool.name}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`
                  flex items-center gap-3 rounded-lg p-3 transition-all duration-300
                  ${status === 'active' ? tool.bgColor : 'hover:bg-muted/50'}
                `}
              >
                {/* Tool Icon */}
                <div className={`
                  flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all
                  ${status === 'completed' ? 'bg-success/10' : status === 'active' ? tool.bgColor : 'bg-muted'}
                `}>
                  {status === 'completed' ? (
                    <CheckCircle className="h-5 w-5 text-success" />
                  ) : status === 'active' ? (
                    <Loader2 className={`h-5 w-5 animate-spin ${tool.activeColor}`} />
                  ) : (
                    <Icon className="h-5 w-5 text-muted-foreground" />
                  )}
                </div>

                {/* Tool Info */}
                <div className="flex-1 min-w-0">
                  <div className={`font-medium ${
                    status === 'active' ? 'text-foreground' : 
                    status === 'completed' ? 'text-foreground' : 'text-muted-foreground'
                  }`}>
                    {tool.label}
                  </div>
                  <AnimatePresence mode="wait">
                    {message && status === 'completed' && (
                      <motion.p
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="text-sm text-muted-foreground truncate"
                      >
                        {message}
                      </motion.p>
                    )}
                    {status === 'active' && (
                      <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-sm text-muted-foreground"
                      >
                        Processing...
                      </motion.p>
                    )}
                  </AnimatePresence>
                </div>

                {/* Status Badge */}
                {status === 'completed' && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="shrink-0 rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success"
                  >
                    Done
                  </motion.div>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Live Insights Preview */}
        {(headlinesCount > 0 || priceDataPoints > 0 || sentiment) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-6 mb-4 rounded-lg border border-dashed border-primary/30 bg-primary/5 p-4"
          >
            <div className="mb-2 text-xs font-medium uppercase tracking-wider text-primary">
              Live Insights
            </div>
            <div className="grid grid-cols-3 gap-4 text-center">
              {headlinesCount > 0 && (
                <div>
                  <div className="text-2xl font-bold text-foreground">{headlinesCount}</div>
                  <div className="text-xs text-muted-foreground">Headlines</div>
                </div>
              )}
              {priceDataPoints > 0 && (
                <div>
                  <div className="text-2xl font-bold text-foreground">{priceDataPoints}</div>
                  <div className="text-xs text-muted-foreground">Price Points</div>
                </div>
              )}
              {sentiment && (
                <div>
                  <div className={`text-lg font-bold ${
                    sentiment === 'Bullish' ? 'text-success' :
                    sentiment === 'Bearish' ? 'text-destructive' : 'text-muted-foreground'
                  }`}>
                    {sentiment}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {confidence ? `${Math.round(confidence * 100)}% conf` : 'Sentiment'}
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
            className="mx-6 mb-4 rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive"
          >
            {error}
          </motion.div>
        )}

        {/* Cancel Button */}
        {isStreaming && onCancel && (
          <div className="border-t border-border px-6 py-4">
            <Button
              variant="outline"
              onClick={onCancel}
              className="w-full gap-2"
            >
              <X className="h-4 w-4" />
              Cancel Analysis
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
