import { motion } from 'framer-motion';
import { 
  TrendingUp, 
  TrendingDown, 
  Scale, 
  AlertTriangle,
  CheckCircle,
  Target,
  Shield,
  Zap,
  MessageSquare
} from 'lucide-react';
import { cn } from '../utils/cn';

interface Catalyst {
  description: string;
  timeframe: string;
  probability: number;
  potential_impact: string;
}

interface Risk {
  description: string;
  category: string;
  severity: string;
  probability: number;
  timeframe: string;
}

interface Rebuttal {
  target_claim: string;
  counter_argument: string;
  counter_evidence: string | null;
  strength: number;
}

interface BullCase {
  ticker: string;
  thesis: string;
  catalysts: Catalyst[];
  key_metrics: Record<string, any>;
  upside_reasoning: string;
  confidence: number;
  weaknesses: string[];
  key_claims: Array<{statement: string; evidence: string; confidence: number}>;
}

interface BearCase {
  ticker: string;
  thesis: string;
  risks: Risk[];
  red_flags: string[];
  key_metrics: Record<string, any>;
  downside_reasoning: string;
  confidence: number;
  what_would_make_bullish: string[];
  key_claims: Array<{statement: string; evidence: string; confidence: number}>;
}

interface Verdict {
  ticker: string;
  analysis_id: string;
  timestamp: string;
  scenario_probabilities: {
    bull: number;
    base: number;
    bear: number;
  };
  recommendation: string;
  conviction: number;
  argument_strength: {
    bull: number;
    bear: number;
  };
  decisive_factors: string[];
  unresolved_questions: string[];
  debate_summary: {
    bull: string;
    bear: string;
    synthesis: string;
  };
}

interface DebateData {
  ticker: string;
  analysis_type: string;
  verdict: Verdict;
  bull_case: BullCase;
  bear_case: BearCase;
  rebuttals: {
    bear_to_bull: Rebuttal[];
    bull_to_bear: Rebuttal[];
  };
  timestamp: string;
}

interface DebateViewProps {
  data: DebateData;
}

const getRecommendationColor = (rec: string) => {
  switch (rec) {
    case 'Strong Buy': return 'text-bull bg-bull/10 border-bull/30';
    case 'Buy': return 'text-bull/80 bg-bull/5 border-bull/20';
    case 'Hold': return 'text-txt-muted bg-surface-2 border-border-base';
    case 'Sell': return 'text-bear/80 bg-bear/5 border-bear/20';
    case 'Strong Sell': return 'text-bear bg-bear/10 border-bear/30';
    default: return 'text-txt-muted bg-surface-2 border-border-base';
  }
};

const ScenarioProbabilityBar = ({ 
  bullProb, 
  baseProb, 
  bearProb 
}: { 
  bullProb: number; 
  baseProb: number; 
  bearProb: number;
}) => {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-micro font-mono uppercase tracking-widest text-txt-muted font-bold">
        <span>BULL_CASE</span>
        <span>BASE_CASE</span>
        <span>BEAR_CASE</span>
      </div>
      <div className="h-[3px] w-full flex rounded-none overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${bullProb * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="bg-bull h-full"
          title={`Bull: ${(bullProb * 100).toFixed(0)}%`}
        />
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${baseProb * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
          className="bg-txt-muted/30 h-full"
          title={`Base: ${(baseProb * 100).toFixed(0)}%`}
        />
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${bearProb * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          className="bg-bear h-full"
          title={`Bear: ${(bearProb * 100).toFixed(0)}%`}
        />
      </div>
      <div className="flex justify-between text-micro font-mono font-bold">
        <span className="text-bull">{(bullProb * 100).toFixed(0)}%</span>
        <span className="text-txt-muted">{(baseProb * 100).toFixed(0)}%</span>
        <span className="text-bear">{(bearProb * 100).toFixed(0)}%</span>
      </div>
    </div>
  );
};

const AgentCard = ({ 
  type, 
  thesis, 
  confidence, 
  items,
  rebuttals
}: { 
  type: 'bull' | 'bear';
  thesis: string;
  confidence: number;
  items: Array<{label: string; value: string}>;
  rebuttals: Rebuttal[];
}) => {
  const isBull = type === 'bull';
  
  return (
    <motion.div
      initial={{ opacity: 0, x: isBull ? -20 : 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: isBull ? 0.2 : 0.4 }}
    >
      <div className={cn(
        "border rounded-sm overflow-hidden bg-surface-1",
        isBull ? "border-bull/30" : "border-bear/30"
      )}>
        {/* Header */}
        <div className={cn(
          "border-b px-4 py-3 flex items-center justify-between",
          isBull ? "border-bull/20 bg-bull/5" : "border-bear/20 bg-bear/5"
        )}>
          <div className="flex items-center gap-2">
            {isBull ? (
              <TrendingUp className="h-4 w-4 text-bull" />
            ) : (
              <TrendingDown className="h-4 w-4 text-bear" />
            )}
            <h3 className="text-sm font-mono font-bold tracking-widest uppercase text-txt-primary">
              {isBull ? 'BULL_CASE' : 'BEAR_CASE'}
            </h3>
          </div>
          <span className={cn(
            "text-micro font-mono font-bold tracking-widest uppercase border px-2 py-0.5 rounded-sm",
            isBull ? "text-bull border-bull/30" : "text-bear border-bear/30"
          )}>
            {(confidence * 100).toFixed(0)}% CONF
          </span>
        </div>

        {/* Thesis */}
        <div className="px-4 py-3 border-b border-border-base/50 bg-canvas">
          <p className="text-sm font-serif text-txt-secondary leading-relaxed italic">
            "{thesis}"
          </p>
        </div>

        {/* Key Points */}
        <div className="p-4 bg-canvas space-y-3">
          <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-txt-primary flex items-center gap-2">
            {isBull ? <Target className="h-3 w-3 text-bull" /> : <Shield className="h-3 w-3 text-bear" />}
            {isBull ? 'KEY_CATALYSTS' : 'KEY_RISKS'}
          </h4>
          <ul className="space-y-1.5">
            {items.slice(0, 3).map((item, i) => (
              <li key={i} className="text-micro font-mono text-txt-secondary flex items-start gap-2 tracking-wider uppercase">
                <span className={cn(
                  "mt-1.5 h-1.5 w-1.5 rounded-sm shrink-0",
                  isBull ? "bg-bull" : "bg-bear"
                )} />
                <span><strong className="text-txt-primary">{item.label}:</strong> {item.value}</span>
              </li>
            ))}
          </ul>
        </div>
        
        {/* Rebuttals Received */}
        {rebuttals.length > 0 && (
          <div className="p-4 border-t border-border-base/50 bg-surface-2/30 space-y-2">
            <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-accent flex items-center gap-2">
              <MessageSquare className="h-3 w-3" />
              REBUTTALS_RECEIVED
            </h4>
            {rebuttals.slice(0, 2).map((r, i) => (
              <div key={i} className="border border-border-base/50 bg-surface-1 p-3 rounded-sm">
                <p className="text-micro font-serif text-txt-muted italic tracking-wider">"{r.target_claim}"</p>
                <p className="mt-1.5 text-micro font-mono text-txt-secondary uppercase tracking-wider">{r.counter_argument}</p>
                <span className="inline-block mt-1.5 text-micro font-mono text-accent border border-accent/30 px-1.5 py-0.5 rounded-sm uppercase tracking-widest font-bold">
                  STRENGTH: {(r.strength * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default function DebateView({ data }: DebateViewProps) {
  const { verdict, bull_case, bear_case, rebuttals } = data;
  
  // Prepare bull items
  const bullItems = bull_case.catalysts?.map(c => ({
    label: c.timeframe,
    value: c.description
  })) || [];
  
  // Prepare bear items
  const bearItems = bear_case.risks?.map(r => ({
    label: r.category,
    value: r.description
  })) || [];

  return (
    <div className="space-y-6">
      {/* Verdict Banner */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-border-base/50 bg-surface-2 flex items-center gap-3">
            <Scale className="h-4 w-4 text-accent" />
            <h2 className="text-sm font-mono font-bold tracking-widest uppercase text-txt-primary">
              {data.ticker} // ADVERSARIAL_ANALYSIS
            </h2>
          </div>
          
          <div className="p-4 bg-canvas">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-4">
              <div className="flex flex-col gap-1">
                <span className="text-micro font-mono text-txt-muted uppercase tracking-widest">
                  REBUTTALS_EXCHANGED: {rebuttals?.bear_to_bull?.length || 0}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className={cn(
                  "text-sm font-mono font-bold tracking-widest uppercase border px-3 py-1.5 rounded-sm",
                  getRecommendationColor(verdict.recommendation)
                )}>
                  {verdict.recommendation}
                </span>
                <span className="text-micro font-mono text-txt-muted uppercase tracking-widest">
                  CONVICTION: <strong className="text-txt-primary">{(verdict.conviction * 100).toFixed(0)}%</strong>
                </span>
              </div>
            </div>
            
            {/* Scenario Probability Bar */}
            <ScenarioProbabilityBar 
              bullProb={verdict.scenario_probabilities.bull}
              baseProb={verdict.scenario_probabilities.base}
              bearProb={verdict.scenario_probabilities.bear}
            />
          </div>
        </div>
      </motion.div>

      {/* Bull vs Bear - Side by Side */}
      <div className="grid md:grid-cols-2 gap-4">
        <AgentCard 
          type="bull"
          thesis={bull_case.thesis}
          confidence={bull_case.confidence}
          items={bullItems}
          rebuttals={rebuttals?.bear_to_bull || []}
        />
        <AgentCard 
          type="bear"
          thesis={bear_case.thesis}
          confidence={bear_case.confidence}
          items={bearItems}
          rebuttals={rebuttals?.bull_to_bear || []}
        />
      </div>

      {/* Synthesis & Decisive Factors */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
      >
        <div className="border border-border-base bg-surface-1 rounded-sm overflow-hidden">
          <div className="border-b border-border-base/50 bg-surface-2 px-4 py-3 flex items-center gap-2">
            <Zap className="h-4 w-4 text-accent" />
            <h3 className="text-sm font-mono font-bold tracking-widest uppercase text-txt-primary">
              SYNTHESIS_AND_FACTORS
            </h3>
          </div>
          <div className="p-4 bg-canvas space-y-4">
            <p className="text-sm font-serif text-txt-secondary leading-relaxed italic border-l-2 border-border-strong pl-3">
              {verdict.debate_summary?.synthesis || "No synthesis available."}
            </p>
            
            <div className="grid md:grid-cols-2 gap-4">
              {/* Decisive Factors */}
              <div className="space-y-2 border border-border-base/50 bg-surface-1 p-3 rounded-sm">
                <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-bull flex items-center gap-2">
                  <CheckCircle className="h-3 w-3" />
                  DECISIVE_FACTORS
                </h4>
                <ul className="space-y-1">
                  {verdict.decisive_factors?.map((f, i) => (
                    <li key={i} className="text-micro font-mono text-txt-secondary flex items-start gap-2 tracking-wider uppercase">
                      <span className="text-bull shrink-0">&gt;</span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
              
              {/* Unresolved Questions */}
              <div className="space-y-2 border border-border-base/50 bg-surface-1 p-3 rounded-sm">
                <h4 className="text-micro font-mono font-bold uppercase tracking-widest text-accent flex items-center gap-2">
                  <AlertTriangle className="h-3 w-3" />
                  UNRESOLVED_QUESTIONS
                </h4>
                <ul className="space-y-1">
                  {verdict.unresolved_questions?.map((q, i) => (
                    <li key={i} className="text-micro font-mono text-txt-secondary flex items-start gap-2 tracking-wider uppercase">
                      <span className="text-accent shrink-0">?</span>
                      {q}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
