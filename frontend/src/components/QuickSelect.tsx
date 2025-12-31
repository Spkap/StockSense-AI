import { TrendingUp } from 'lucide-react';
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
  { symbol: 'GOOGL', name: 'Google' },
  { symbol: 'AMZN', name: 'Amazon' },
  { symbol: 'TSLA', name: 'Tesla' },
];

const QuickSelect = ({ onSelect, disabled = false }: QuickSelectProps) => {
  return (
    <div className="h-full rounded-2xl border border-border bg-card p-5 shadow-sm transition-all hover:shadow-md">
      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-success/10 text-success">
          <TrendingUp className="h-4 w-4" />
        </div>
        <span className="font-semibold text-foreground">Trending Now</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {popularTickers.map(({ symbol }) => (
          <Button
            key={symbol}
            variant="ghost"
            onClick={() => onSelect(symbol)}
            disabled={disabled}
            className={cn(
              "h-9 rounded-full bg-muted/50 px-4 text-sm font-medium transition-all hover:bg-primary hover:text-primary-foreground",
              "border border-transparent hover:border-primary/20"
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
