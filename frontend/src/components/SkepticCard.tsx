import { AlertTriangle, Scale, TrendingDown, CheckCircle, HelpCircle, AlertCircle } from 'lucide-react';
import { cn } from '../utils/cn';
import type { AnalysisData, Critique, BearCase } from '../types/api';

interface SkepticCardProps {
  data?: AnalysisData;
}

// Skeptic verdict styling using Obsidian tokens
const skepticConfig = {
  'Disagree': {
    color: 'text-kill',
    bgColor: 'bg-kill/10',
    borderColor: 'border-kill/30',
    icon: AlertCircle,
    label: 'DISAGREES',
  },
  'Partially Disagree': {
    color: 'text-accent',
    bgColor: 'bg-accent/10',
    borderColor: 'border-accent/30',
    icon: AlertTriangle,
    label: 'PARTIAL_DISAGREEMENT',
  },
  'Agree with Reservations': {
    color: 'text-bear',
    bgColor: 'bg-bear/10',
    borderColor: 'border-bear/30',
    icon: Scale,
    label: 'CAUTIOUS_AGREEMENT',
  },
  'Agree': {
    color: 'text-bull',
    bgColor: 'bg-bull/10',
    borderColor: 'border-bull/30',
    icon: CheckCircle,
    label: 'AGREES',
  },
};

const SkepticCard = ({ data }: SkepticCardProps) => {
  // Check if we have skeptic data (skeptic_sentiment is truthy)
  const hasSkepticData = Boolean(data?.skeptic_sentiment);
  
  if (!hasSkepticData || !data) {
    return (
      <div className="flex flex-col border border-dashed border-border-strong bg-surface-1 p-8 rounded-sm items-center justify-center min-h-[250px] text-center opacity-80">
        <HelpCircle className="h-6 w-6 text-txt-muted mb-4" />
        <p className="font-mono text-micro tracking-widest text-txt-secondary uppercase font-bold">
          SKEPTIC_LOGS_UNAVAILABLE
        </p>
        <p className="font-mono text-micro text-txt-muted uppercase mt-2 tracking-widest">
          INITIATE_FRESH_SCAN_FOR_CONTRARIAN_DATA
        </p>
      </div>
    );
  }

  const sentiment = data.skeptic_sentiment as keyof typeof skepticConfig;
  const config = skepticConfig[sentiment] || skepticConfig['Agree with Reservations'];
  const Icon = config.icon;

  return (
    <div className="flex flex-col border border-border-base bg-surface-1 rounded-sm w-full overflow-hidden">
      {/* Header with skeptic verdict */}
      <div className="flex items-center justify-between border-b border-border-base/50 px-5 py-4 bg-surface-2/50 relative overflow-hidden">
        
        {/* Subtle warning stripe if disagree */}
        {(sentiment === 'Disagree' || sentiment === 'Partially Disagree') && (
           <div className="absolute top-0 left-0 right-0 h-1 bg-[repeating-linear-gradient(45deg,var(--kill),var(--kill)_10px,transparent_10px,transparent_20px)] opacity-20" />
        )}

        <div className="flex items-center gap-3 relative z-10">
          <div className={cn("flex h-8 w-8 items-center justify-center rounded-sm border", config.bgColor, config.borderColor, config.color)}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex flex-col">
            <h4 className={cn("text-sm font-mono font-bold tracking-widest leading-none", config.color)}>
              {config.label}
            </h4>
            <span className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1.5">
              SKEPTIC_VERDICT
            </span>
          </div>
        </div>
        <div className="flex flex-col items-end relative z-10">
          <span className={cn("text-xl font-mono font-bold tracking-tight leading-none", config.color)}>
            {Math.round((data.skeptic_confidence || 0) * 100)}%
          </span>
          <span className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1.5">
            CRITIQUE_STR
          </span>
        </div>
      </div>

      <div className="p-4 flex flex-col gap-6">
        {/* Primary Disagreement */}
        {data.primary_disagreement && (
          <div className="border border-kill/30 bg-kill/10 p-4 rounded-sm border-l-[3px] border-l-kill">
            <span className="text-micro font-mono font-bold text-kill uppercase tracking-widest mb-2 block">PRI_DISAGREEMENT</span>
            <p className="text-micro font-mono text-txt-primary leading-relaxed uppercase tracking-wider">
              {data.primary_disagreement}
            </p>
          </div>
        )}

        {/* Bear Cases */}
        {data.bear_cases && data.bear_cases.length > 0 && (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2 border-b border-border-base/50 pb-1">
              <TrendingDown className="h-3 w-3 text-bear" />
              <h5 className="text-micro font-mono font-bold text-txt-primary uppercase tracking-widest">BEAR_CASES</h5>
            </div>
            <div className="flex flex-col gap-2">
              {data.bear_cases.map((bearCase: BearCase, index: number) => {
                const severityConfig = {
                  'High': { color: 'text-kill', bg: 'bg-kill/10', border: 'border-kill/30' },
                  'Medium': { color: 'text-accent', bg: 'bg-accent/10', border: 'border-accent/30' },
                  'Low': { color: 'text-txt-muted', bg: 'bg-surface-3', border: 'border-border-strong' }
                }[bearCase.severity] || { color: 'text-txt-muted', bg: 'bg-surface-2', border: 'border-border-base/50' };
                
                return (
                  <div key={index} className="flex flex-col border border-border-base/50 bg-surface-2/30 p-2 rounded-sm gap-2">
                    <div className="flex items-start justify-between gap-4">
                      <span className="text-micro font-mono text-txt-secondary leading-relaxed uppercase tracking-widest">{bearCase.argument}</span>
                      <span className={cn("text-micro font-mono uppercase tracking-widest px-1.5 py-0.5 rounded-sm shrink-0 border", severityConfig.bg, severityConfig.color, severityConfig.border)}>
                        {bearCase.severity}
                      </span>
                    </div>
                    {bearCase.trigger && (
                      <div className="flex gap-2 items-center bg-surface-1 p-1.5 px-2 rounded-sm border border-border-base/50 mt-1">
                        <span className="text-micro font-mono text-txt-muted uppercase tracking-widest font-bold shrink-0">TRIGGER:</span>
                        <span className="text-micro font-mono text-txt-secondary leading-tight uppercase tracking-widest">{bearCase.trigger}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Critiques */}
        {data.critiques && data.critiques.length > 0 && (
          <div className="flex flex-col gap-3">
            <h5 className="text-micro font-mono font-bold text-txt-primary uppercase tracking-widest border-b border-border-base/50 pb-1">KEY_CRITIQUES</h5>
            <ul className="flex flex-col gap-3">
              {data.critiques.map((critique: Critique, index: number) => (
                <li key={index} className="flex flex-col gap-1.5 border-l-2 border-border-strong pl-3">
                  <span className="text-micro font-mono text-txt-primary leading-relaxed uppercase tracking-widest">{critique.critique}</span>
                  {critique.assumption_challenged && (
                    <span className="text-micro font-mono text-txt-muted uppercase tracking-widest opacity-80">
                      // CHALLENGES_ASSUMPTION: {critique.assumption_challenged}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Hidden Risks */}
        {data.hidden_risks && data.hidden_risks.length > 0 && (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2 border-b border-border-base/50 pb-1">
              <AlertTriangle className="h-3 w-3 text-accent" />
              <h5 className="text-micro font-mono font-bold text-accent uppercase tracking-widest">HIDDEN_RISKS</h5>
            </div>
            <ul className="flex flex-col gap-2 mt-1">
              {data.hidden_risks.map((risk: string, index: number) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-accent text-micro mt-0.5 font-bold">{`>`}</span>
                  <span className="text-micro font-mono text-txt-secondary leading-relaxed uppercase tracking-widest">{risk}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* What Would Change Mind */}
        {data.would_change_mind && data.would_change_mind.length > 0 && (
          <div className="flex flex-col gap-3 pt-4 border-t border-border-base/50">
            <div className="flex items-center gap-2 border-b border-border-base/50 pb-1">
              <CheckCircle className="h-3 w-3 text-bull" />
              <h5 className="text-micro font-mono font-bold text-bull uppercase tracking-widest">
                INVALIDATION_CRITERIA
              </h5>
            </div>
            <ul className="flex flex-col gap-2 mt-1">
              {data.would_change_mind.map((item: string, index: number) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="text-bull text-micro mt-0.5 font-bold uppercase tracking-widest shrink-0">{`[ OK ]`}</span>
                  <span className="text-micro font-mono text-txt-secondary leading-relaxed uppercase tracking-widest">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default SkepticCard;
