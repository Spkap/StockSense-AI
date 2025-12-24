import { useState, useEffect } from 'react';
import { Progress } from './ui/progress';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Loader2, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AnalysisProgressProps {
  ticker: string;
  onCancel?: () => void;
}

const analysisSteps = [
  { label: 'Connecting to Agent...', duration: 2000 },
  { label: 'Fetching headlines...', duration: 4000 },
  { label: 'Retrieving price data...', duration: 3000 },
  { label: 'Analyzing sentiment...', duration: 8000 },
  { label: 'Generating insights...', duration: 5000 },
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

  const currentLabel = analysisSteps[currentStep]?.label || 'Processing...';

  return (
    <Card className="mx-auto max-w-2xl border-none bg-card/50 shadow-none backdrop-blur">
      <CardContent className="flex flex-col items-center justify-center py-16 md:py-20">
        <div className="mb-6 rounded-full bg-primary/10 p-4">
          <Loader2 className="h-10 w-10 animate-spin text-primary" />
        </div>
        
        <h2 className="mb-2 text-2xl font-bold tracking-tight text-foreground md:text-3xl">
          {ticker}
        </h2>
        <p className="mb-8 text-muted-foreground">
          Analyzing market data...
        </p>

        <div className="w-full max-w-sm space-y-4">
          <Progress value={progress} className="h-2" />
          
          <div className="h-6 text-center">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentStep}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -5 }}
                className="text-sm font-medium text-foreground"
              >
                {currentLabel}
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        <div className="mt-8 flex gap-2">
          {analysisSteps.map((_, index) => (
            <div
              key={index}
              className={`h-2 w-2 rounded-full transition-colors ${
                index <= currentStep ? 'bg-primary' : 'bg-muted'
              }`}
            />
          ))}
        </div>

        {/* Cancel Button */}
        {onCancel && (
          <Button
            variant="outline"
            onClick={onCancel}
            className="mt-8 gap-2"
          >
            <X className="h-4 w-4" />
            Cancel Analysis
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default AnalysisProgress;
