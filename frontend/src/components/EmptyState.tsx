import { 
  LineChart, 
  Search, 
  Newspaper,
  Sparkles,
  TrendingUp,
  Brain,
  Clock,
  Command
} from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { cn } from '../utils/cn';

interface EmptyStateProps {
  type: 'welcome' | 'no-chart' | 'no-news' | 'no-history';
  onAction?: () => void;
}

const emptyStateConfig = {
  welcome: {
    icon: Sparkles,
    title: 'Welcome to StockSense',
    description: 'AI-powered stock analysis at your fingertips.',
    actionLabel: null,
    showFeatures: true,
  },
  'no-chart': {
    icon: LineChart,
    title: 'No Data Available',
    description: 'Price data is currently unavailable for this stock.',
    actionLabel: 'Try Again',
    showFeatures: false,
  },
  'no-news': {
    icon: Newspaper,
    title: 'No Headlines',
    description: 'No recent news articles were found for this ticker.',
    actionLabel: null,
    showFeatures: false,
  },
  'no-history': {
    icon: Search,
    title: 'No History',
    description: "You haven't analyzed any stocks yet. Start by entering a ticker above.",
    actionLabel: null,
    showFeatures: false,
  },
};

const features = [
  {
    icon: Brain,
    title: 'AI Analysis',
    description: 'Sentiment analysis of news headlines',
  },
  {
    icon: TrendingUp,
    title: 'Price Charts',
    description: 'Historical price visualization',
  },
  {
    icon: Clock,
    title: 'Real-time',
    description: 'Fresh data from market sources',
  },
];

// Detect if user is on Mac for keyboard shortcut display
const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

const EmptyState = ({ type, onAction }: EmptyStateProps) => {
  const config = emptyStateConfig[type];
  const Icon = config.icon;

  return (
    <Card className={cn(
      "flex h-full flex-col items-center justify-center p-6 text-center border-border bg-card",
      type !== 'welcome' && "border-dashed"
    )}>
      <CardContent className="flex flex-col items-center pt-6">
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-primary/20 to-primary/5 border border-primary/20">
          <Icon className="h-8 w-8 text-primary" />
        </div>
        
        <h3 className="mb-2 text-xl font-bold tracking-tight text-foreground">
          {config.title}
        </h3>
        
        <p className="max-w-[320px] text-sm text-muted-foreground mb-6">
          {config.description}
        </p>

        {/* Features Grid for Welcome State */}
        {config.showFeatures && (
          <div className="grid grid-cols-3 gap-4 mb-6 w-full max-w-md">
            {features.map((feature) => {
              const FeatureIcon = feature.icon;
              return (
                <div key={feature.title} className="flex flex-col items-center gap-2 p-3 rounded-lg bg-muted/50">
                  <FeatureIcon className="h-5 w-5 text-muted-foreground" />
                  <span className="text-xs font-medium text-foreground">{feature.title}</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Keyboard Shortcut Hint for Welcome State */}
        {type === 'welcome' && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground/70">
            <span>Press</span>
            <kbd className="inline-flex items-center gap-0.5 rounded border border-border bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium">
              {isMac ? (
                <>
                  <Command className="h-2.5 w-2.5" />
                  <span>K</span>
                </>
              ) : (
                <span>Ctrl+K</span>
              )}
            </kbd>
            <span>to search</span>
          </div>
        )}

        {config.actionLabel && onAction && (
          <Button 
            variant="outline" 
            className="mt-6"
            onClick={onAction}
          >
            {config.actionLabel}
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

export default EmptyState;
