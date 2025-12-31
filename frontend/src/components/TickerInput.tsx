import { useState, FormEvent, useMemo, forwardRef, useImperativeHandle, useRef } from 'react';
import { Search, AlertCircle, Command, ArrowRight } from 'lucide-react';
import { Card } from './ui/card';
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

const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

const TickerInput = forwardRef<TickerInputRef, TickerInputProps>(({ onAnalyze, disabled = false }, ref) => {
  const [ticker, setTicker] = useState('');
  const [touched, setTouched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validation = useMemo(() => validateTickerFormat(ticker), [ticker]);
  const showError = touched && ticker.length > 0 && !validation.isValid && validation.error;

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
    const filtered = value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 5);
    setTicker(filtered);
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="relative group">
        <div className={cn(
          "absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-primary/20 to-primary/10 opacity-0 blur transition duration-500",
          ticker.length > 0 && "opacity-100"
        )} />
        <form
          onSubmit={handleSubmit}
          className={cn(
            "relative flex items-center gap-2 rounded-2xl bg-background p-2 ring-1 ring-border transition-all duration-300",
            "focus-within:ring-2 focus-within:ring-primary/20 focus-within:shadow-lg"
          )}
        >
          <Search className="ml-3 h-5 w-5 text-muted-foreground" />

          <Input
            ref={inputRef}
            placeholder="Search for a stock..."
            value={ticker}
            onChange={(e) => handleChange(e.target.value)}
            onBlur={() => setTouched(true)}
            disabled={disabled}
            maxLength={5}
            className={cn(
              "h-12 border-none bg-transparent px-2 text-lg font-medium placeholder:text-muted-foreground/50 focus-visible:ring-0",
              "uppercase tracking-wide placeholder:normal-case placeholder:tracking-normal"
            )}
            aria-invalid={showError ? 'true' : 'false'}
          />

          {/* Keyboard Shortcut Hint */}
          <div className="hidden items-center gap-1 rounded-md border bg-muted px-2 py-1 text-xs font-medium text-muted-foreground sm:flex">
            {isMac ? <Command className="h-3 w-3" /> : <span>Ctrl</span>}
            <span>K</span>
          </div>

          <Button
            type="submit"
            size="icon"
            disabled={disabled || !ticker.trim() || !validation.isValid}
            className={cn(
              "h-10 w-10 shrink-0 rounded-xl transition-all duration-300",
              ticker.length > 0 ? "bg-primary text-primary-foreground opacity-100" : "bg-muted text-muted-foreground opacity-50"
            )}
          >
            <ArrowRight className="h-5 w-5" />
          </Button>
        </form>
      </div>

      {showError && (
        <div className="ml-2 flex items-center gap-1.5 text-sm text-destructive animate-in slide-in-from-top-1 fade-in duration-200">
          <AlertCircle className="h-4 w-4" />
          <span>{validation.error}</span>
        </div>
      )}
    </div>
  );
});

TickerInput.displayName = 'TickerInput';

export default TickerInput;
