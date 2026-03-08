import { TrendingUp, TrendingDown, Minus, AlertTriangle, Info, HelpCircle } from 'lucide-react';
import { cn } from '../utils/cn';
import type { AnalysisData, KeyTheme } from '../types/api';

interface SentimentCardProps {
  // New: Accept full analysis data for structured display
  data?: AnalysisData;
  // Legacy: Fallback for report-only mode
  report?: string;
}

// Sentiment configuration for visual styling using Obsidian tokens
const sentimentConfig = {
  Bullish: {
    color: 'text-bull',
    bgColor: 'bg-bull/10',
    borderColor: 'border-bull/30',
    icon: TrendingUp,
    label: 'BULLISH',
    progressColor: 'bg-bull',
  },
  Bearish: {
    color: 'text-bear',
    bgColor: 'bg-bear/10',
    borderColor: 'border-bear/30',
    icon: TrendingDown,
    label: 'BEARISH',
    progressColor: 'bg-bear',
  },
  Neutral: {
    color: 'text-accent',
    bgColor: 'bg-accent/10',
    borderColor: 'border-accent/30',
    icon: Minus,
    label: 'NEUTRAL',
    progressColor: 'bg-accent',
  },
  'Insufficient Data': {
    color: 'text-txt-muted',
    bgColor: 'bg-surface-2',
    borderColor: 'border-border-base',
    icon: HelpCircle,
    label: 'INSUFFICIENT_DATA',
    progressColor: 'bg-txt-muted',
  },
};

// Legacy fallback: keyword-based sentiment extraction (for cached data without structured fields)
function extractLegacySentiment(report: string): {
  sentiment: 'Bullish' | 'Bearish' | 'Neutral' | 'Insufficient Data';
  confidence: number;
} {
  const lowerReport = report.toLowerCase();
  
  const positiveWords = ['positive', 'bullish', 'strong', 'growth', 'optimistic', 'gains', 'buy', 'upgrade'];
  const negativeWords = ['negative', 'bearish', 'weak', 'decline', 'pessimistic', 'losses', 'sell', 'downgrade'];
  
  let positiveScore = 0;
  let negativeScore = 0;
  
  positiveWords.forEach(word => {
    const matches = lowerReport.match(new RegExp(word, 'gi'));
    if (matches) positiveScore += matches.length;
  });
  
  negativeWords.forEach(word => {
    const matches = lowerReport.match(new RegExp(word, 'gi'));
    if (matches) negativeScore += matches.length;
  });
  
  const total = positiveScore + negativeScore;
  
  if (positiveScore > negativeScore) {
    return { sentiment: 'Bullish', confidence: total > 0 ? Math.min((positiveScore / total), 0.85) : 0.5 };
  } else if (negativeScore > positiveScore) {
    return { sentiment: 'Bearish', confidence: total > 0 ? Math.min((negativeScore / total), 0.85) : 0.5 };
  }
  return { sentiment: 'Neutral', confidence: 0.5 };
}

const SentimentCard = ({ data, report }: SentimentCardProps) => {
  // Determine if we have structured data from backend
  const hasStructuredData = data?.overall_sentiment && data.overall_confidence !== undefined;
  
  // Extract sentiment info (prefer structured, fallback to legacy)
  let sentiment: 'Bullish' | 'Bearish' | 'Neutral' | 'Insufficient Data';
  let confidence: number;
  let confidenceReasoning: string | undefined;
  let keyThemes: KeyTheme[] = [];
  let risksIdentified: string[] = [];
  let informationGaps: string[] = [];
  let potentialImpact: string | undefined;
  
  if (hasStructuredData && data) {
    sentiment = data.overall_sentiment as typeof sentiment;
    confidence = data.overall_confidence ?? 0;
    confidenceReasoning = data.confidence_reasoning;
    keyThemes = data.key_themes ?? [];
    risksIdentified = data.risks_identified ?? [];
    informationGaps = data.information_gaps ?? [];
    potentialImpact = data.potential_impact;
  } else if (report) {
    const legacy = extractLegacySentiment(report);
    sentiment = legacy.sentiment;
    confidence = legacy.confidence;
  } else {
    sentiment = 'Insufficient Data';
    confidence = 0;
  }
  
  const config = sentimentConfig[sentiment] || sentimentConfig['Insufficient Data'];
  const Icon = config.icon;
  
  return (
    <div className="flex flex-col border border-border-base bg-surface-1 rounded-sm w-full overflow-hidden">
      {/* Header with sentiment and score */}
      <div className="flex items-center justify-between border-b border-border-base px-5 py-4 bg-surface-2/50">
        <div className="flex items-center gap-3">
          <div className={cn("flex h-8 w-8 items-center justify-center rounded-sm border", config.bgColor, config.borderColor, config.color)}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <h4 className={cn("text-sm font-mono font-bold tracking-widest leading-none", config.color)}>
              {config.label}
            </h4>
            <span className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1.5">
              {hasStructuredData ? 'SYS_ANALYSIS' : 'EST_ANALYSIS'}
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <span className="text-xl font-mono font-bold tracking-tight text-txt-primary leading-none">
            {Math.round(confidence * 100)}%
          </span>
          <span className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1.5">
            CONF_LVL
          </span>
        </div>
      </div>

      {/* Confidence progress bar */}
      <div className="h-[2px] w-full bg-surface-3">
        <div 
          className={cn("h-full transition-all duration-500 ease-out", config.progressColor)} 
          style={{ width: `${confidence * 100}%` }} 
        />
      </div>
      
      <div className="p-4 flex flex-col gap-5">
        {/* Confidence reasoning */}
        {hasStructuredData && confidenceReasoning && (
          <div className="border border-border-base/50 bg-surface-2 p-3 rounded-sm">
            <div className="flex items-start gap-3">
              <Info className="h-3 w-3 text-txt-muted mt-0.5 shrink-0" />
              <p className="text-micro font-mono text-txt-secondary leading-relaxed uppercase tracking-wider">
                {confidenceReasoning}
              </p>
            </div>
          </div>
        )}
        
        {/* Market Impact */}
        {potentialImpact && potentialImpact !== '' && (
          <div className="flex items-center justify-between border border-border-base/50 bg-surface-2 px-3 py-2 rounded-sm">
            <span className="text-micro font-mono text-txt-muted uppercase tracking-widest">EXP_IMPACT</span>
            <span className="text-micro font-mono text-txt-primary uppercase tracking-widest">{potentialImpact}</span>
          </div>
        )}

        {/* Key Themes */}
        {hasStructuredData && keyThemes.length > 0 && (
          <div className="flex flex-col gap-3">
            <h5 className="text-micro font-mono font-bold text-txt-primary uppercase tracking-widest border-b border-border-base/50 pb-1">MARKET_THEMES</h5>
            <div className="flex flex-col gap-2">
              {keyThemes.slice(0, 3).map((theme, index) => (
                <div key={index} className="flex items-start justify-between gap-4 py-1">
                  <span className="text-micro font-mono text-txt-secondary leading-relaxed uppercase tracking-widest">{theme.theme}</span>
                  <span className={cn(
                    "text-micro font-mono uppercase tracking-widest px-1.5 py-0.5 rounded-sm shrink-0 border",
                    theme.sentiment_direction === 'Bullish' && "bg-bull/10 text-bull border-bull/30",
                    theme.sentiment_direction === 'Bearish' && "bg-bear/10 text-bear border-bear/30",
                    theme.sentiment_direction === 'Mixed' && "bg-accent/10 text-accent border-accent/30"
                  )}>
                    {theme.sentiment_direction}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Risks Identified */}
        {hasStructuredData && risksIdentified.length > 0 && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 border-b border-border-base/50 pb-1">
              <AlertTriangle className="h-3 w-3 text-bear" />
              <h5 className="text-micro font-mono font-bold text-bear uppercase tracking-widest">IDENTIFIED_RISKS</h5>
            </div>
            <ul className="flex flex-col gap-2">
              {risksIdentified.slice(0, 3).map((risk, index) => (
                <li key={index} className="flex gap-3">
                  <span className="text-bear text-micro mt-0.5 font-bold">{`>`}</span>
                  <span className="text-micro font-mono text-txt-secondary leading-relaxed uppercase tracking-widest">{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Information Gaps - Epistemic Honesty */}
        {hasStructuredData && informationGaps.length > 0 && (
          <div className="flex flex-col gap-3 pt-4 border-t border-border-base/50">
            <div className="flex items-center gap-2 border-b border-border-base/50 pb-1">
              <HelpCircle className="h-3 w-3 text-txt-muted" />
              <h5 className="text-micro font-mono text-txt-muted uppercase tracking-widest">BLIND_SPOTS</h5>
            </div>
            <ul className="flex flex-col gap-2 mt-1">
              {informationGaps.slice(0, 2).map((gap, index) => (
                <li key={index} className="flex gap-3">
                  <span className="text-txt-muted text-micro mt-0.5">{`>`}</span>
                  <span className="text-micro font-mono text-txt-muted uppercase tracking-widest leading-relaxed">{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Legacy mode indicator */}
        {!hasStructuredData && report && (
          <div className="pt-4 border-t border-border-base/50 text-center text-micro font-mono text-txt-muted uppercase tracking-widest opacity-50">
            --- LEGACY_CACHE_MODE ---
          </div>
        )}
      </div>
    </div>
  );
};

export default SentimentCard;
