import { AlertTriangle, Scale, TrendingDown, CheckCircle, HelpCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { cn } from '../utils/cn';
import type { AnalysisData, Critique, BearCase } from '../types/api';

interface SkepticCardProps {
  data?: AnalysisData;
}

// Skeptic verdict styling
const skepticConfig = {
  'Disagree': {
    color: 'text-destructive',
    bgColor: 'bg-destructive/10',
    icon: AlertCircle,
    label: 'Skeptic Disagrees',
  },
  'Partially Disagree': {
    color: 'text-warning',
    bgColor: 'bg-warning/10',
    icon: AlertTriangle,
    label: 'Partial Disagreement',
  },
  'Agree with Reservations': {
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    icon: Scale,
    label: 'Cautious Agreement',
  },
  'Agree': {
    color: 'text-success',
    bgColor: 'bg-success/10',
    icon: CheckCircle,
    label: 'Skeptic Agrees',
  },
};

const SkepticCard = ({ data }: SkepticCardProps) => {
  // Check if we have skeptic data (skeptic_sentiment is truthy)
  const hasSkepticData = Boolean(data?.skeptic_sentiment);
  
  if (!hasSkepticData || !data) {
    return (
      <Card className="h-full border-dashed border-muted-foreground/30 bg-muted/20">
        <CardContent className="p-6 flex flex-col items-center justify-center min-h-[200px] text-center">
          <HelpCircle className="h-8 w-8 text-muted-foreground/50 mb-3" />
          <p className="text-sm text-muted-foreground">
            Skeptic analysis will appear here when available
          </p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Run a fresh analysis to generate contrarian perspective
          </p>
        </CardContent>
      </Card>
    );
  }

  const sentiment = data.skeptic_sentiment as keyof typeof skepticConfig;
  const config = skepticConfig[sentiment] || skepticConfig['Agree with Reservations'];
  const Icon = config.icon;

  return (
    <Card className="h-full border-border bg-card shadow-sm">
      <CardContent className="p-6">
        {/* Header with skeptic verdict */}
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
                Skeptic&apos;s Verdict
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className={cn("text-3xl font-bold tracking-tighter", config.color)}>
              {Math.round((data.skeptic_confidence || 0) * 100)}%
            </span>
            <p className="text-[10px] text-muted-foreground uppercase tracking-wider">
              Critique Strength
            </p>
          </div>
        </div>

        {/* Primary Disagreement */}
        {data.primary_disagreement && (
          <div className="mb-4 p-3 rounded-lg bg-destructive/5 border border-destructive/20">
            <p className="text-sm font-medium text-foreground">
              {data.primary_disagreement}
            </p>
          </div>
        )}

        {/* Bear Cases */}
        {data.bear_cases && data.bear_cases.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1 mb-2">
              <TrendingDown className="h-3.5 w-3.5 text-destructive" />
              <span className="text-xs text-destructive font-medium uppercase tracking-wider">Bear Cases</span>
            </div>
            <div className="space-y-2">
              {data.bear_cases.slice(0, 2).map((bearCase: BearCase, index: number) => {
                const severityColor = {
                  'High': 'bg-destructive text-destructive-foreground',
                  'Medium': 'bg-warning text-warning-foreground',
                  'Low': 'bg-muted text-muted-foreground'
                }[bearCase.severity] || 'bg-muted';
                
                return (
                  <div key={index} className="p-2 rounded bg-muted/30">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-sm text-foreground">{bearCase.argument}</span>
                      <Badge className={cn("text-[10px] shrink-0", severityColor)}>
                        {bearCase.severity}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Trigger: {bearCase.trigger}
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Critiques */}
        {data.critiques && data.critiques.length > 0 && (
          <div className="mb-4">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wider mb-2">
              Key Critiques
            </p>
            <ul className="space-y-1">
              {data.critiques.slice(0, 2).map((critique: Critique, index: number) => (
                <li key={index} className="text-sm text-muted-foreground">
                  <span className="text-foreground font-medium">{critique.critique}</span>
                  {critique.assumption_challenged && (
                    <span className="text-xs text-muted-foreground/80 ml-1">
                      (challenges: {critique.assumption_challenged})
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Hidden Risks */}
        {data.hidden_risks && data.hidden_risks.length > 0 && (
          <div className="mb-4">
            <div className="flex items-center gap-1 mb-2">
              <AlertTriangle className="h-3 w-3 text-warning" />
              <span className="text-xs text-warning font-medium uppercase tracking-wider">Hidden Risks</span>
            </div>
            <ul className="space-y-1">
              {data.hidden_risks.slice(0, 2).map((risk: string, index: number) => (
                <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                  <span className="text-warning">•</span>
                  <span>{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* What Would Change Mind */}
        {data.would_change_mind && data.would_change_mind.length > 0 && (
          <div className="pt-3 border-t border-border">
            <div className="flex items-center gap-1 mb-2">
              <CheckCircle className="h-3 w-3 text-success" />
              <span className="text-xs text-success font-medium uppercase tracking-wider">
                Would Change Skeptic&apos;s Mind
              </span>
            </div>
            <ul className="space-y-1">
              {data.would_change_mind.slice(0, 2).map((item: string, index: number) => (
                <li key={index} className="text-xs text-muted-foreground flex items-start gap-2">
                  <span className="text-success">✓</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SkepticCard;
