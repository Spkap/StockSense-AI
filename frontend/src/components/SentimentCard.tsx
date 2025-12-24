import { TrendingUp, TrendingDown, Minus, AlertTriangle, Info, HelpCircle } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { cn } from '../utils/cn';
import type { AnalysisData, KeyTheme } from '../types/api';

interface SentimentCardProps {
  // New: Accept full analysis data for structured display
  data?: AnalysisData;
  // Legacy: Fallback for report-only mode
  report?: string;
}

// Sentiment configuration for visual styling
const sentimentConfig = {
  Bullish: {
    color: 'text-success',
    bgColor: 'bg-success/10',
    borderColor: 'border-success/20',
    icon: TrendingUp,
    label: 'Bullish',
    progressColor: 'bg-success',
  },
  Bearish: {
    color: 'text-destructive',
    bgColor: 'bg-destructive/10',
    borderColor: 'border-destructive/20',
    icon: TrendingDown,
    label: 'Bearish',
    progressColor: 'bg-destructive',
  },
  Neutral: {
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    borderColor: 'border-warning/20',
    icon: Minus,
    label: 'Neutral',
    progressColor: 'bg-warning',
  },
  'Insufficient Data': {
    color: 'text-muted-foreground',
    bgColor: 'bg-muted/50',
    borderColor: 'border-muted',
    icon: HelpCircle,
    label: 'Insufficient Data',
    progressColor: 'bg-muted-foreground',
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
    <Card className="h-full border-border bg-card shadow-sm">
      <CardContent className="p-6">
        {/* Header with sentiment and score */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={cn("flex h-12 w-12 items-center justify-center rounded-xl transition-colors", config.bgColor, config.color)}>
              <Icon className="h-6 w-6" />
            </div>
            <div>
              <h4 className="text-lg font-bold text-foreground leading-tight">
                {config.label}
              </h4>
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                {hasStructuredData ? 'AI Sentiment' : 'Estimated Sentiment'}
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className={cn("text-3xl font-bold tracking-tighter", config.color)}>
              {Math.round(confidence * 100)}%
            </span>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Confidence
            </p>
          </div>
        </div>

        {/* Confidence progress bar */}
        <div className="mb-4">
          <div className="h-2.5 w-full overflow-hidden rounded-full bg-secondary">
            <div 
              className={cn("h-full transition-all duration-500 ease-out", config.progressColor)} 
              style={{ width: `${confidence * 100}%` }} 
            />
          </div>
        </div>
        
        {/* Confidence reasoning (only if structured data available) */}
        {hasStructuredData && confidenceReasoning && (
          <div className="mb-4 p-3 rounded-lg bg-muted/50">
            <div className="flex items-start gap-2">
              <Info className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
              <p className="text-sm text-muted-foreground leading-relaxed">
                {confidenceReasoning}
              </p>
            </div>
          </div>
        )}
        
        {/* Market Impact (if available) */}
        {potentialImpact && potentialImpact !== '' && (
          <div className="mb-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground font-medium">Expected Impact</span>
              <Badge variant="outline" className="text-xs">
                {potentialImpact}
              </Badge>
            </div>
          </div>
        )}

        {/* Key Themes (only if structured data available) */}
        {hasStructuredData && keyThemes.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-2">
              Key Themes
            </p>
            <div className="space-y-2">
              {keyThemes.slice(0, 3).map((theme, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <span className="text-foreground">{theme.theme}</span>
                  <Badge 
                    variant="secondary"
                    className={cn(
                      "text-[10px]",
                      theme.sentiment_direction === 'Bullish' && "bg-success/10 text-success",
                      theme.sentiment_direction === 'Bearish' && "bg-destructive/10 text-destructive",
                      theme.sentiment_direction === 'Mixed' && "bg-warning/10 text-warning"
                    )}
                  >
                    {theme.sentiment_direction}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Risks Identified (only if structured data available) */}
        {hasStructuredData && risksIdentified.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1 mb-2">
              <AlertTriangle className="h-3 w-3 text-warning" />
              <span className="text-xs text-warning font-medium uppercase tracking-wider">Risks</span>
            </div>
            <ul className="space-y-1">
              {risksIdentified.slice(0, 3).map((risk, index) => (
                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-warning">•</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Information Gaps - Epistemic Honesty (only if structured data available) */}
        {hasStructuredData && informationGaps.length > 0 && (
          <div className="pt-3 border-t border-border">
            <div className="flex items-center gap-1 mb-2">
              <HelpCircle className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">
                What We Don&apos;t Know
              </span>
            </div>
            <ul className="space-y-1">
              {informationGaps.slice(0, 2).map((gap, index) => (
                <li key={index} className="text-xs text-muted-foreground/80 italic flex items-start gap-2">
                  <span>•</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Legacy mode indicator */}
        {!hasStructuredData && report && (
          <div className="pt-3 border-t border-border">
            <p className="text-[10px] text-muted-foreground/60 text-center italic">
              Legacy analysis mode — run fresh analysis for structured insights
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SentimentCard;
