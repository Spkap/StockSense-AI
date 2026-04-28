import { useEffect, useState } from 'react';
import { BookOpen, ChevronDown, ChevronRight, Clock, AlertTriangle, Target, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';

import { useAuth } from '../context/AuthContext';
import { useTheses, useThesisHistory, useThesisComparison } from '../api/theses';
import { useThesisCheckStream } from '../hooks/useThesisCheckStream';
import ThesisEditor from '../components/ThesisEditor';
import ThesisCheckPanel from '../components/ThesisCheckPanel';
import type { Thesis } from '../types/thesis';
import type { AnalysisData } from '../types/api';
import { cn } from '../utils/cn';
import { motion, AnimatePresence } from 'framer-motion';
import ThesisComparisonBanner from '../components/ThesisComparisonBanner';

const CONVICTION_STYLES = {
  low: 'bg-muted text-muted-foreground border-border/40',
  medium: 'bg-warning/10 text-warning border-warning/20',
  high: 'bg-success/10 text-success border-success/20',
};

const STATUS_STYLES = {
  active: 'bg-primary/10 text-primary border-primary/20',
  validated: 'bg-success/10 text-success border-success/20',
  invalidated: 'bg-destructive/10 text-destructive border-destructive/20',
  exited: 'bg-muted text-muted-foreground border-border/40',
};

function ThesisCard({ thesis, onEdit, enabled }: { thesis: Thesis; onEdit: () => void; enabled: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const { data: historyData } = useThesisHistory(expanded ? thesis.id : null, enabled);
  const { data: comparison } = useThesisComparison(expanded ? thesis.id : null, enabled);
  const thesisCheck = useThesisCheckStream();

  const statusStyle = STATUS_STYLES[thesis.status] || STATUS_STYLES.active;

  useEffect(() => {
    if (!expanded || !enabled) return;
    thesisCheck.loadLatest(thesis.id);
  }, [enabled, expanded, thesis.id, thesisCheck.loadLatest]);

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "group overflow-hidden rounded-xl border border-border/50 bg-card transition-all duration-300",
        expanded ? "shadow-lg ring-1 ring-primary/5" : "hover:shadow-md hover:border-primary/20"
      )}
    >
      <div className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4">
            {/* Ticker Symbol */}
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/5 text-lg font-bold text-foreground transition-colors group-hover:bg-primary/10">
              {thesis.ticker}
            </div>
            
            <div className="space-y-1">
              <h3 className="font-semibold text-foreground">{thesis.ticker} Thesis</h3>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                <span>Updated {new Date(thesis.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2 md:flex-row md:items-center">
            <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium uppercase tracking-wider", CONVICTION_STYLES[thesis.conviction_level])}>
              {thesis.conviction_level} Conviction
            </span>
            <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium uppercase tracking-wider", statusStyle)}>
              {thesis.status}
            </span>
          </div>
        </div>

        {/* Thesis Summary */}
        <div className="mt-4 pl-16">
           <p className={cn("text-sm text-muted-foreground leading-relaxed", !expanded && "line-clamp-2")}>
             {thesis.thesis_summary}
           </p>
        </div>
      
        {/* Actions / Expand Toggle */}
        <div className="mt-4 flex items-center justify-between pl-16">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 rounded-full text-xs font-medium text-primary hover:bg-primary/10"
          >
            {expanded ? (
              <>Less Details <ChevronDown className="h-3 w-3" /></>
            ) : (
              <>More Details <ChevronRight className="h-3 w-3" /></>
            )}
          </Button>
          
          <Button variant="ghost" size="sm" onClick={onEdit} className="h-7 text-xs">
            Edit
          </Button>
        </div>
      </div>

      {/* Expanded Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border/50 bg-secondary/5 px-5 py-4 pl-20"
          >
            <div className="space-y-6">
              {/* Kill Criteria */}
              {thesis.kill_criteria.length > 0 && (
                <div>
                  <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                    <Target className="h-3 w-3" />
                    Kill Criteria
                  </h4>
                  <ul className="space-y-2">
                    {thesis.kill_criteria.map((criteria, i) => (
                      <li key={i} className="flex items-start gap-3 text-sm text-foreground/90 bg-background/50 p-2 rounded-md border border-border/40">
                        <AlertTriangle className="h-4 w-4 text-warning mt-0.5 shrink-0" />
                        <span>{criteria}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* History */}
              {historyData && historyData.history.length > 0 && (
                <div>
                  <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-3">
                    Change Log
                  </h4>
                  <div className="space-y-3 pl-1 border-l-2 border-border/40 ml-1">
                    {historyData.history.slice(0, 5).map((entry) => (
                      <div key={entry.id} className="relative pl-4 text-xs">
                        <div className="absolute -left-[5px] top-1.5 h-2 w-2 rounded-full bg-border" />
                        <div className="flex flex-col gap-0.5">
                            <span className="font-medium text-foreground">{entry.change_type.replace('_', ' ')}</span>
                            <span className="text-muted-foreground">{new Date(entry.created_at).toLocaleDateString()}</span>
                            {entry.change_reason && (
                                <p className="text-muted-foreground/80 italic mt-0.5">"{entry.change_reason}"</p>
                            )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <ThesisCheckPanel
                ticker={thesis.ticker}
                isStreaming={thesisCheck.isStreaming}
                progress={thesisCheck.progress}
                phase={thesisCheck.phase}
                events={thesisCheck.events}
                finalData={thesisCheck.finalData}
                runBundle={thesisCheck.runBundle}
                error={thesisCheck.error}
                onStart={() => thesisCheck.start(thesis.id)}
                onStop={thesisCheck.stop}
                onCorrect={thesisCheck.recordCorrection}
              />

              <ThesisComparisonBanner comparison={comparison ?? null} />

              <div className="grid gap-3 text-xs text-muted-foreground md:grid-cols-3">
                <div className="rounded-lg border border-border/40 bg-background/50 p-3">
                  <div className="font-semibold uppercase tracking-wider text-foreground/70">Time Horizon</div>
                  <div className="mt-1 capitalize">{thesis.time_horizon}</div>
                </div>
                <div className="rounded-lg border border-border/40 bg-background/50 p-3">
                  <div className="font-semibold uppercase tracking-wider text-foreground/70">Thesis Type</div>
                  <div className="mt-1 capitalize">{thesis.thesis_type.replace('_', ' ')}</div>
                </div>
                <div className="rounded-lg border border-border/40 bg-background/50 p-3">
                  <div className="font-semibold uppercase tracking-wider text-foreground/70">Linked Analysis</div>
                  <div className="mt-1">{thesis.origin_analysis_id ? `Analysis #${thesis.origin_analysis_id}` : 'Not linked'}</div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

interface ThesesPageProps {
  onBack: () => void;
  initialTicker?: string | null;
  initialAnalysisData?: AnalysisData | null;
  openCreateSignal?: number;
}

export default function ThesesPage({ onBack, initialTicker, initialAnalysisData, openCreateSignal = 0 }: ThesesPageProps) {
  const { user } = useAuth();
  const { data, isLoading, error } = useTheses(undefined, !!user);
  const [editingThesis, setEditingThesis] = useState<Thesis | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [draftTicker, setDraftTicker] = useState(initialTicker ?? '');

  useEffect(() => {
    setDraftTicker(initialTicker ?? '');
  }, [initialTicker]);

  useEffect(() => {
    if (!openCreateSignal || !initialTicker) return;
    setEditingThesis(null);
    setDraftTicker(initialTicker);
    setShowEditor(true);
  }, [initialTicker, openCreateSignal]);

  if (!user) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center p-6 text-center">
        <div className="mb-4 rounded-full bg-muted/30 p-4 backdrop-blur-sm">
          <BookOpen className="h-8 w-8 text-muted-foreground" />
        </div>
        <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
        <p className="max-w-xs text-sm text-muted-foreground mb-6">
          Sign in to access your private investment theses and track your performance.
        </p>
        <Button onClick={onBack} variant="secondary">
          Return to Thesis Desk
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-muted-foreground hover:text-foreground cursor-pointer transition-colors" onClick={onBack}>
            <ArrowLeft className="h-4 w-4" />
            <span className="text-sm font-medium">Back</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">My Theses</h1>
          <p className="text-muted-foreground">
            Manage your high-conviction ideas and monitor kill criteria
          </p>
        </div>
        <Button onClick={onBack} className="hidden md:flex">
          New Analysis
        </Button>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4 text-destructive">
          Failed to load theses: {error.message}
        </div>
      )}

      {/* Thesis List */}
      <div className="space-y-4">
        {isLoading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="h-32 w-full animate-pulse rounded-xl bg-muted/40" />
          ))
        ) : data && data.theses.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-3xl border border-dashed border-border/50 py-24 text-center">
            <div className="mb-4 rounded-full bg-secondary/50 p-6">
                 <BookOpen className="h-10 w-10 text-muted-foreground/40" />
            </div>
            <h3 className="text-lg font-semibold">No theses yet</h3>
            <p className="max-w-sm text-sm text-muted-foreground mt-2 mb-6">
              Start by analyzing a stock ticker, then save your thesis to track its performance over time.
            </p>
            <Button onClick={onBack}>
              Start New Analysis
            </Button>
          </div>
        ) : (
          data?.theses.map((thesis) => (
            <ThesisCard
              key={thesis.id}
              thesis={thesis}
              enabled={!!user}
              onEdit={() => {
                setEditingThesis(thesis);
                setShowEditor(true);
              }}
            />
          ))
        )}
      </div>

      {/* Thesis Editor Modal */}
      <ThesisEditor
        isOpen={showEditor}
        onClose={() => {
          setShowEditor(false);
          setEditingThesis(null);
        }}
        ticker={editingThesis?.ticker || draftTicker}
        existingThesis={editingThesis}
        analysisData={editingThesis ? null : initialAnalysisData}
      />
    </div>
  );
}
