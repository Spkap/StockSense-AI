import { useState, FormEvent, useMemo, forwardRef, useImperativeHandle, useRef } from 'react';
import { AlertCircle, Command } from 'lucide-react';
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
    return { isValid: false, error: 'TICKER MUST BE 5 CHARACTERS OR LESS' };
  }
  
  if (!TICKER_PATTERN.test(normalized)) {
    return { isValid: false, error: 'ONLY LETTERS A-Z ALLOWED' };
  }
  
  return { isValid: true, error: null };
}

// Detect if user is on Mac for keyboard shortcut display
const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

const TickerInput = forwardRef<TickerInputRef, TickerInputProps>(({ onAnalyze, disabled = false }, ref) => {
  const [ticker, setTicker] = useState('');
  const [touched, setTouched] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
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
      inputRef.current?.blur();
    }
  };

  const handleChange = (value: string) => {
    // Only allow letters and limit to 5 characters
    const filtered = value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 5);
    setTicker(filtered);
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Input
            ref={inputRef}
            placeholder="INPUT_TICKER"
            value={ticker}
            onChange={(e) => handleChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => {
              setTouched(true);
              setIsFocused(false);
            }}
            disabled={disabled}
            maxLength={5}
            className={cn(
              "h-12 bg-surface-1 border border-border-base font-mono text-sm uppercase tracking-widest text-txt-primary placeholder:text-txt-muted/50 rounded-sm pl-4 pr-16 outline-none transition-colors",
              isFocused && "bg-surface-2 border-txt-secondary",
              showError && "border-bear text-bear"
            )}
            aria-invalid={showError ? 'true' : 'false'}
            aria-describedby={showError ? 'ticker-error' : undefined}
          />
          {/* Keyboard shortcut hint */}
          <div className={cn(
            "absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-micro font-mono tracking-widest text-txt-muted transition-opacity",
            isFocused ? "opacity-0" : "opacity-100"
          )}>
            {isMac ? (
              <>
                <Command className="h-3 w-3" />
                <span>K</span>
              </>
            ) : (
              <span>CTRL+K</span>
            )}
          </div>
        </div>
        
        <Button 
          type="submit" 
          disabled={disabled || !ticker.trim() || !validation.isValid}
          className="h-12 min-w-[120px] bg-accent text-canvas hover:bg-accent/90 font-mono font-bold text-micro uppercase tracking-widest rounded-sm disabled:opacity-50 disabled:bg-surface-2 disabled:text-txt-muted transition-colors border border-transparent disabled:border-border-base"
        >
          EXECUTE
        </Button>
      </form>
      
      {/* Validation Error Message */}
      {showError && (
        <div id="ticker-error" className="mt-2 flex items-center gap-2 text-micro uppercase tracking-widest text-bear font-mono">
          <AlertCircle className="h-3 w-3" />
          <span>{validation.error}</span>
        </div>
      )}
    </div>
  );
});

TickerInput.displayName = 'TickerInput';

export default TickerInput;
