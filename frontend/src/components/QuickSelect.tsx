import { Button } from './ui/button';
import { cn } from '../utils/cn';

interface QuickSelectProps {
  onSelect: (ticker: string) => void;
  disabled?: boolean;
}

const popularTickers = [
  { symbol: 'AAPL', name: 'Apple' },
  { symbol: 'MSFT', name: 'Microsoft' },
  { symbol: 'NVDA', name: 'NVIDIA' },
  { symbol: 'TSLA', name: 'Tesla' },
  { symbol: 'GOOGL', name: 'Google' },
];

const QuickSelect = ({ onSelect, disabled = false }: QuickSelectProps) => {
  return (
    <div className="flex h-12 w-full items-center gap-2 overflow-x-auto px-4 no-scrollbar border border-border-base rounded-sm bg-surface-1">
      <div className="flex items-center gap-2 border-r border-border-base/50 pr-4 mr-2">
          <div className="w-1 h-3 bg-accent" />
          <span className="text-micro font-mono text-txt-muted uppercase tracking-widest shrink-0">
            QUICK_SEL
          </span>
      </div>
      <div className="flex gap-2">
        {popularTickers.map(({ symbol }) => (
          <Button
            key={symbol}
            variant="ghost"
            onClick={() => onSelect(symbol)}
            disabled={disabled}
            className={cn(
              "h-7 px-3 py-1 font-mono text-micro tracking-widest text-txt-secondary hover:text-txt-primary hover:bg-surface-2 border border-transparent hover:border-border-strong transition-colors shrink-0 rounded-sm uppercase"
            )}
          >
            {symbol}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default QuickSelect;
