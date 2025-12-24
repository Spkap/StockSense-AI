import { useState, FormEvent, useMemo, forwardRef, useImperativeHandle, useRef } from 'react';
import { Search, AlertCircle, Command } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { cn } from '../utils/cn';

interface TickerInputProps {
  onAnalyze: (ticker: string) => void;
  disabled?: boolean;
}

export interface TickerInputRef {
  focus: () => void;
}

// Regex pattern for valid ticker format (1-5 uppercase letters)
const TICKER_PATTERN = /^[A-Z]{1,5}$/;

function validateTickerFormat(ticker: string): { isValid: boolean; error: string | null } {
  if (!ticker) {
    return { isValid: false, error: null };
  }
  
  const normalized = ticker.toUpperCase().trim();
  
  if (normalized.length > 5) {
    return { isValid: false, error: 'Ticker must be 5 characters or less' };
  }
  
  if (!TICKER_PATTERN.test(normalized)) {
    return { isValid: false, error: 'Only letters A-Z allowed' };
  }
  
  return { isValid: true, error: null };
}

// Detect if user is on Mac for keyboard shortcut display
const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

const TickerInput = forwardRef<TickerInputRef, TickerInputProps>(({ onAnalyze, disabled = false }, ref) => {
  const [ticker, setTicker] = useState('');
  const [touched, setTouched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validation = useMemo(() => validateTickerFormat(ticker), [ticker]);
  const showError = touched && ticker.length > 0 && !validation.isValid && validation.error;

  // Expose focus method to parent
  useImperativeHandle(ref, () => ({
    focus: () => {
      inputRef.current?.focus();
    }
  }));

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const normalized = ticker.trim().toUpperCase();
    
    if (normalized && validation.isValid) {
      onAnalyze(normalized);
      setTicker('');
      setTouched(false);
    }
  };

  const handleChange = (value: string) => {
    // Only allow letters and limit to 5 characters
    const filtered = value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 5);
    setTicker(filtered);
  };

  return (
    <Card className="h-full border-border bg-card shadow-sm transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle>Analyze Stock</CardTitle>
        <CardDescription>Enter a ticker symbol to generate AI insights.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-2">
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                ref={inputRef}
                placeholder="e.g. AAPL, TSLA"
                value={ticker}
                onChange={(e) => handleChange(e.target.value)}
                onBlur={() => setTouched(true)}
                disabled={disabled}
                maxLength={5}
                className={cn(
                  "pl-9 pr-16 font-semibold uppercase tracking-wider text-foreground placeholder:normal-case placeholder:tracking-normal",
                  showError && "border-destructive focus-visible:ring-destructive"
                )}
                aria-invalid={showError ? 'true' : 'false'}
                aria-describedby={showError ? 'ticker-error' : undefined}
              />
              {/* Keyboard shortcut hint */}
              <div className="absolute right-3 top-1/2 -translate-y-1/2 hidden sm:flex items-center gap-0.5 text-xs text-muted-foreground/60">
                {isMac ? (
                  <>
                    <Command className="h-3 w-3" />
                    <span>K</span>
                  </>
                ) : (
                  <span className="text-[10px]">Ctrl+K</span>
                )}
              </div>
            </div>
            <Button 
              type="submit" 
              disabled={disabled || !ticker.trim() || !validation.isValid}
              className="min-w-[100px] font-semibold"
            >
              Analyze
            </Button>
          </div>
          
          {/* Validation Error Message */}
          {showError && (
            <div id="ticker-error" className="flex items-center gap-1 text-xs text-destructive">
              <AlertCircle className="h-3 w-3" />
              <span>{validation.error}</span>
            </div>
          )}
        </form>
      </CardContent>
    </Card>
  );
});

TickerInput.displayName = 'TickerInput';

export default TickerInput;
