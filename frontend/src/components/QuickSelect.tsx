import { TrendingUp } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';

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
    <Card className="h-full border-border bg-card shadow-sm transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center rounded-full bg-success/10 p-2 text-success">
            <TrendingUp className="h-4 w-4" />
          </div>
          <CardTitle className="text-sm font-semibold text-foreground">Trending Stocks</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-wrap gap-2">
          {popularTickers.map(({ symbol }) => (
            <Button
              key={symbol}
              variant="secondary"
              size="sm"
              onClick={() => onSelect(symbol)}
              disabled={disabled}
              className="rounded-full bg-secondary/50 font-medium hover:bg-secondary hover:text-secondary-foreground"
            >
              {symbol}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default QuickSelect;
