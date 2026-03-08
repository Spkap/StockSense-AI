/**
 * AnalysisProgress - Fallback progress display (non-streaming)
 * 
 * Obsidian Terminal styled — monochrome, dense, mechanical.
 */

import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Loader2, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AnalysisProgressProps {
  ticker: string;
  onCancel?: () => void;
}

const analysisSteps = [
  { label: 'CONNECTING_AGENT' },
  { label: 'FETCH_HEADLINES' },
  { label: 'FETCH_PRICE_DATA' },
  { label: 'ANALYZE_SENTIMENT' },
  { label: 'GENERATE_INSIGHTS' },
];

const AnalysisProgress = ({ ticker, onCancel }: AnalysisProgressProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev < analysisSteps.length - 1 ? prev + 1 : prev));
    }, 4000);

    const progressInterval = setInterval(() => {
      setProgress((prev) => (prev >= 95 ? prev : prev + Math.random() * 3));
    }, 500);

    return () => {
      clearInterval(stepInterval);
      clearInterval(progressInterval);
    };
  }, []);

  const currentLabel = analysisSteps[currentStep]?.label || 'PROCESSING';

  return (
    <div className="mx-auto max-w-2xl border border-border-base bg-surface-1 rounded-sm overflow-hidden font-mono">
      <div className="flex flex-col items-center justify-center py-16 md:py-20 bg-canvas">
        <div className="mb-6 rounded-sm bg-accent/10 p-4 border border-accent/20">
          <Loader2 className="h-8 w-8 animate-spin text-accent" />
        </div>
        
        <h2 className="mb-2 text-2xl font-mono font-bold tracking-tight text-txt-primary">
          {ticker}
        </h2>
        <p className="mb-8 text-micro font-mono text-txt-muted uppercase tracking-widest">
          Analyzing market data...
        </p>

        <div className="w-full max-w-sm space-y-4 px-4">
          {/* Progress Bar */}
          <div className="h-[2px] w-full bg-surface-2 rounded-none overflow-hidden">
            <motion.div
              className="h-full bg-accent"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            />
          </div>
          
          {/* Step Label */}
          <div className="h-6 text-center">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="text-micro font-mono font-bold uppercase tracking-widest text-txt-secondary"
              >
                {'>'} {currentLabel}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Step Indicators */}
        <div className="mt-8 flex gap-2">
          {analysisSteps.map((_, index) => (
            <div
              key={index}
              className={`h-1.5 w-1.5 rounded-sm transition-colors ${
                index <= currentStep ? 'bg-accent' : 'bg-surface-2'
              }`}
            />
          ))}
        </div>

        {/* Cancel Button */}
        {onCancel && (
          <Button
            variant="ghost"
            onClick={onCancel}
            className="mt-8 gap-2 font-mono text-micro uppercase tracking-widest text-txt-muted hover:text-kill hover:bg-kill-dim border border-transparent hover:border-kill/30 rounded-sm"
          >
            <X className="h-3 w-3" />
            ABORT_SEQ
          </Button>
        )}
      </div>
    </div>
  );
};

export default AnalysisProgress;
