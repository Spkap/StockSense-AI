import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
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
    case 'Strong Buy': return 'text-success bg-success/10 border-success/20';
    case 'Buy': return 'text-success/80 bg-success/5 border-success/10';
    case 'Hold': return 'text-muted-foreground bg-muted border-border';
    case 'Sell': return 'text-destructive/80 bg-destructive/5 border-destructive/10';
    case 'Strong Sell': return 'text-destructive bg-destructive/10 border-destructive/20';
    default: return 'text-muted-foreground bg-muted border-border';
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
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Bull Case</span>
        <span>Base Case</span>
        <span>Bear Case</span>
      </div>
      <div className="h-4 w-full flex rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${bullProb * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="bg-success h-full"
          title={`Bull: ${(bullProb * 100).toFixed(0)}%`}
        />
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${baseProb * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
          className="bg-muted-foreground/30 h-full"
          title={`Base: ${(baseProb * 100).toFixed(0)}%`}
        />
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${bearProb * 100}%` }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
          className="bg-destructive h-full"
          title={`Bear: ${(bearProb * 100).toFixed(0)}%`}
        />
      </div>
      <div className="flex justify-between text-xs font-semibold">
        <span className="text-success">{(bullProb * 100).toFixed(0)}%</span>
        <span className="text-muted-foreground">{(baseProb * 100).toFixed(0)}%</span>
        <span className="text-destructive">{(bearProb * 100).toFixed(0)}%</span>
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
      <Card className={cn(
        "h-full border-2",
        isBull ? "border-success/30" : "border-destructive/30"
      )}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {isBull ? (
                <TrendingUp className="h-5 w-5 text-success" />
              ) : (
                <TrendingDown className="h-5 w-5 text-destructive" />
              )}
              <CardTitle className="text-lg">
                {isBull ? 'Bull Case' : 'Bear Case'}
              </CardTitle>
            </div>
            <Badge 
              variant="outline" 
              className={cn(
                "font-mono",
                isBull ? "text-success border-success/30" : "text-destructive border-destructive/30"
              )}
            >
              {(confidence * 100).toFixed(0)}% confident
            </Badge>
          </div>
          <CardDescription className="mt-2 text-sm">
            {thesis}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Key Points */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold flex items-center gap-1">
              {isBull ? <Target className="h-3 w-3" /> : <Shield className="h-3 w-3" />}
              {isBull ? 'Key Catalysts' : 'Key Risks'}
            </h4>
            <ul className="space-y-1">
              {items.slice(0, 3).map((item, i) => (
                <li key={i} className="text-xs text-muted-foreground flex items-start gap-2">
                  <span className={cn(
                    "mt-1.5 h-1.5 w-1.5 rounded-full shrink-0",
                    isBull ? "bg-success" : "bg-destructive"
                  )} />
                  <span><strong>{item.label}:</strong> {item.value}</span>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Rebuttals Received */}
          {rebuttals.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-border">
              <h4 className="text-sm font-semibold flex items-center gap-1 text-amber-500">
                <MessageSquare className="h-3 w-3" />
                Rebuttals Received
              </h4>
              {rebuttals.slice(0, 2).map((r, i) => (
                <div key={i} className="text-xs bg-muted/50 rounded p-2">
                  <p className="text-muted-foreground italic">"{r.target_claim}"</p>
                  <p className="mt-1 text-foreground">{r.counter_argument}</p>
                  <Badge variant="outline" className="mt-1 text-[10px]">
                    Strength: {(r.strength * 100).toFixed(0)}%
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
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
        <Card className="overflow-hidden">
          <div className="bg-gradient-to-r from-primary/5 via-transparent to-primary/5 p-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-full bg-primary/10">
                  <Scale className="h-6 w-6 text-primary" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold">{data.ticker} Adversarial Analysis</h2>
                  <p className="text-sm text-muted-foreground">
                    Bull and Bear agents debated with {rebuttals?.bear_to_bull?.length || 0} rebuttals
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge 
                  className={cn(
                    "text-lg px-4 py-1 border",
                    getRecommendationColor(verdict.recommendation)
                  )}
                >
                  {verdict.recommendation}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  Conviction: <strong>{(verdict.conviction * 100).toFixed(0)}%</strong>
                </span>
              </div>
            </div>
            
            {/* Scenario Probability Bar */}
            <div className="mt-6">
              <ScenarioProbabilityBar 
                bullProb={verdict.scenario_probabilities.bull}
                baseProb={verdict.scenario_probabilities.base}
                bearProb={verdict.scenario_probabilities.bear}
              />
            </div>
          </div>
        </Card>
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
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              Synthesis & Decisive Factors
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-muted-foreground">
              {verdict.debate_summary?.synthesis || "No synthesis available."}
            </p>
            
            <div className="grid md:grid-cols-2 gap-4">
              {/* Decisive Factors */}
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-1 text-sm">
                  <CheckCircle className="h-4 w-4 text-success" />
                  What Tipped the Balance
                </h4>
                <ul className="space-y-1">
                  {verdict.decisive_factors?.map((f, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-success">•</span>
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
              
              {/* Unresolved Questions */}
              <div className="space-y-2">
                <h4 className="font-semibold flex items-center gap-1 text-sm">
                  <AlertTriangle className="h-4 w-4 text-amber-500" />
                  Unresolved Questions
                </h4>
                <ul className="space-y-1">
                  {verdict.unresolved_questions?.map((q, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                      <span className="text-amber-500">•</span>
                      {q}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
