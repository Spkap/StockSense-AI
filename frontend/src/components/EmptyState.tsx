import { 
  LineChart, 
  Search, 
  Newspaper,
  Sparkles,
  TrendingUp,
  Brain,
  Clock,
  Command,
  Briefcase
} from 'lucide-react';
import { Button } from './ui/button';
import { cn } from '../utils/cn';

interface EmptyStateProps {
  type: 'welcome' | 'no-chart' | 'no-news' | 'no-history' | 'no-data';
  onAction?: () => void;
}

const emptyStateConfig = {
  welcome: {
    icon: Sparkles,
    title: 'STOCKSENSE_SYS_V2.0',
    description: 'AWAITING TICKER INPUT TO INITIALIZE INTELLIGENCE ROUTINES.',
    actionLabel: null,
    showFeatures: true,
  },
  'no-chart': {
    icon: LineChart,
    title: 'NO DATA STREAM',
    description: 'PRICE DATA IS CURRENTLY UNAVAILABLE FOR THIS ASSET.',
    actionLabel: 'RETRY CONNECTION',
    showFeatures: false,
  },
  'no-news': {
    icon: Newspaper,
    title: 'NO SIGNAL DETECTED',
    description: 'NO RECENT SIGNIFICANT PUBLICATIONS FOUND FOR THIS TICKER.',
    actionLabel: null,
    showFeatures: false,
  },
  'no-history': {
    icon: Search,
    title: 'CACHE EMPTY',
    description: "NO PRIOR SCANS FOUND IN LOCAL STORAGE. AWAITING INPUT.",
    actionLabel: null,
    showFeatures: false,
  },
  'no-data': {
    icon: Briefcase,
    title: 'FUNDAMENTALS MISSING',
    description: 'CORE FINANCIAL DATA IS NOT AVAILABLE FOR THIS TICKER.',
    actionLabel: null,
    showFeatures: false,
  },
};

const features = [
  {
    icon: Brain,
    title: 'AI_SYNTHESIS',
  },
  {
    icon: TrendingUp,
    title: 'PRICE_ACTION',
  },
  {
    icon: Clock,
    title: 'REAL_TIME_FEED',
  },
];

// Detect if user is on Mac for keyboard shortcut display
const isMac = typeof navigator !== 'undefined' && navigator.platform.toUpperCase().indexOf('MAC') >= 0;

const EmptyState = ({ type, onAction }: EmptyStateProps) => {
  const config = emptyStateConfig[type];
  const Icon = config.icon;

  return (
    <div className={cn(
      "flex h-full min-h-[400px] flex-col items-center justify-center p-8 text-center border bg-surface-1 rounded-sm relative overflow-hidden",
      type === 'welcome' ? "border-border-base" : "border-dashed border-border-strong opacity-80 bg-surface-1/50"
    )}>
      
      {/* Background terminal grid effect overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none opacity-20"></div>

      <div className="relative z-10 flex flex-col items-center max-w-lg">
        <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-sm bg-accent/5 border border-accent/20">
          <Icon className="h-5 w-5 text-accent animate-pulse" />
        </div>
        
        <h3 className="mb-2 text-micro font-mono font-bold tracking-widest text-txt-primary uppercase">
          {config.title}
        </h3>
        
        <p className="max-w-[360px] font-mono text-micro uppercase tracking-widest leading-relaxed text-txt-muted mb-8">
          {config.description}
        </p>

        {/* Features Grid for Welcome State */}
        {config.showFeatures && (
          <div className="flex flex-wrap gap-2 mb-8 w-full justify-center">
            {features.map((feature) => {
              const FeatureIcon = feature.icon;
              return (
                <div key={feature.title} className="flex items-center gap-2 px-3 py-1.5 border border-border-base bg-surface-2 rounded-sm transition-colors hover:border-border-strong">
                  <FeatureIcon className="h-3 w-3 text-txt-muted" />
                  <span className="text-micro font-mono uppercase tracking-widest text-txt-secondary">{feature.title}</span>
                </div>
              );
            })}
          </div>
        )}

        {/* Keyboard Shortcut Hint for Welcome State */}
        {type === 'welcome' && (
          <div className="flex items-center gap-2 text-micro text-txt-muted font-mono tracking-widest opacity-80 mt-auto pt-8">
            <span>PRESS</span>
            <span className="inline-flex items-center gap-1 border border-border-strong bg-surface-2 px-1.5 py-0.5 rounded-sm">
              {isMac ? (
                <>
                  <Command className="h-3 w-3" />
                  <span>K</span>
                </>
              ) : (
                <span>CTRL+K</span>
              )}
            </span>
            <span>TO INITIATE SCAN</span>
          </div>
        )}

        {config.actionLabel && onAction && (
          <Button 
            variant="ghost" 
            className="mt-6 font-mono text-micro tracking-widest uppercase border border-border-strong text-txt-secondary hover:text-txt-primary hover:bg-surface-2 hover:border-txt-muted rounded-sm h-8"
            onClick={onAction}
          >
            {config.actionLabel}
          </Button>
        )}
      </div>
    </div>
  );
};

export default EmptyState;
