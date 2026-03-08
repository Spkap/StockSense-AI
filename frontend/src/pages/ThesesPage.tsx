import { useState } from 'react';
import { BookOpen, Clock, Target, ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/button';

import { useAuth } from '../context/AuthContext';
import { useTheses, useThesisHistory } from '../api/theses';
import ThesisEditor from '../components/ThesisEditor';
import type { Thesis } from '../types/thesis';
import { cn } from '../utils/cn';
import { motion, AnimatePresence } from 'framer-motion';

const CONVICTION_STYLES = {
  low: 'text-txt-muted border-border-base bg-surface-2',
  medium: 'text-accent border-accent/30 bg-accent/10',
  high: 'text-bull border-bull/30 bg-bull/10',
};

const STATUS_STYLES = {
  active: 'text-accent border-accent/30 bg-accent-dim',
  validated: 'text-bull border-bull/30 bg-bull/10',
  invalidated: 'text-kill border-kill/30 bg-kill-dim',
  exited: 'text-txt-muted border-border-strong bg-surface-3',
};

function ThesisCard({ thesis, onEdit }: { thesis: Thesis; onEdit: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const { data: historyData } = useThesisHistory(expanded ? thesis.id : null);

  const statusStyle = STATUS_STYLES[thesis.status] || STATUS_STYLES.active;

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "group overflow-hidden rounded-sm border bg-surface-1 transition-all duration-300",
        expanded ? "border-border-strong shadow-none" : "border-border-base hover:border-border-strong"
      )}
    >
      <div className="p-5 flex flex-col md:flex-row md:items-start gap-5">
        
        {/* Left Side: Ticker Block */}
        <div className="flex shrink-0 w-24 flex-col items-center justify-center p-3 border border-border-base/50 bg-surface-2/30 rounded-sm">
          <span className="text-xl font-mono font-bold text-txt-primary tracking-tighter">
            {thesis.ticker}
          </span>
          <span className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1">
            TICKER_ID
          </span>
        </div>

        {/* Center: Details & Summary */}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
             <div className="flex items-center gap-3 text-micro font-mono text-txt-tertiary uppercase tracking-widest">
               <div className="flex items-center gap-1.5">
                 <Clock className="h-3 w-3 text-txt-muted" />
                 <span>UPDATED: {new Date(thesis.updated_at).toLocaleDateString()}</span>
               </div>
               <span className="text-border-strong">|</span>
               <span>v{(thesis as any).version || '1.0'}</span>
             </div>

             <div className="flex items-center gap-2">
               <span className={cn("inline-flex items-center rounded-sm border px-2 py-1 text-micro font-mono font-bold uppercase tracking-widest", CONVICTION_STYLES[thesis.conviction_level])}>
                 {thesis.conviction_level}_CONVIC
               </span>
               <span className={cn("inline-flex items-center rounded-sm border px-2 py-1 text-micro font-mono font-bold uppercase tracking-widest", statusStyle)}>
                 {thesis.status}
               </span>
             </div>
          </div>

          <h3 className="font-serif text-lg text-txt-primary mb-2 leading-tight">
            {thesis.ticker} Investment Thesis
          </h3>
          
          <p className={cn("text-sm font-serif text-txt-secondary leading-relaxed", !expanded && "line-clamp-2")}>
            {thesis.thesis_summary}
          </p>

          {!expanded && (
             <div className="mt-4 flex gap-4 text-micro font-mono uppercase tracking-widest">
                <span className="text-txt-muted">KILL_CRI: {thesis.kill_criteria.length}</span>
                <span className="text-txt-muted">REV_LOGS: {historyData?.history?.length || 0}</span>
             </div>
          )}
        </div>
      
        {/* Right Side: Actions */}
        <div className="flex md:flex-col gap-2 shrink-0 md:border-l md:border-border-base/50 md:pl-5">
           <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded(!expanded)}
            className="flex-1 md:flex-none justify-center rounded-sm text-micro font-mono font-bold uppercase tracking-widest text-accent border border-transparent hover:border-accent hover:bg-accent-dim h-8 px-3"
          >
            {expanded ? 'COLLAPSE_VIEW' : 'EXPAND_VIEW'}
          </Button>
          
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onEdit} 
            className="flex-1 md:flex-none justify-center rounded-sm text-micro font-mono tracking-widest uppercase text-txt-secondary border border-border-base hover:bg-surface-2 hover:text-txt-primary h-8 px-3"
          >
            EDIT_THESIS
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
            className="border-t border-border-base/50 bg-surface-2/30 px-5 py-5"
          >
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              
              {/* Left Col: Kill Criteria */}
              <div className="space-y-4">
                <h4 className="flex items-center gap-2 text-micro font-mono font-bold uppercase tracking-widest text-accent border-b border-accent/20 pb-2">
                  <Target className="h-3 w-3" />
                  DEF_KILL_CRITERIA
                </h4>
                
                {thesis.kill_criteria.length > 0 ? (
                  <ul className="flex flex-col gap-2">
                    {thesis.kill_criteria.map((criteria, i) => (
                      <li key={i} className="flex items-start gap-3 bg-surface-1 p-3 rounded-sm border border-kill/20 border-l-2 border-l-kill">
                        <span className="font-mono text-kill text-micro uppercase font-bold mt-0.5 shrink-0">[{i+1}]</span>
                        <span className="text-sm font-serif text-txt-primary leading-relaxed">{criteria}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="text-micro font-mono text-txt-muted uppercase tracking-widest p-4 border border-dashed border-border-base text-center">
                    NO_KILL_CRITERIA_DEFINED
                  </div>
                )}
              </div>

              {/* Right Col: History */}
              <div className="space-y-4">
                <h4 className="flex items-center gap-2 text-micro font-mono font-bold uppercase tracking-widest text-txt-primary border-b border-border-base/50 pb-2">
                  <Clock className="h-3 w-3 text-txt-muted" />
                  REVISION_LOGS
                </h4>
                
                {historyData && historyData.history.length > 0 ? (
                  <div className="flex flex-col pl-2 border-l border-border-base">
                    {historyData.history.slice(0, 5).map((entry) => (
                      <div key={entry.id} className="relative pl-5 py-2 group">
                        {/* Timeline dot */}
                        <div className="absolute -left-[5px] top-3.5 h-[9px] w-[9px] rounded-sm bg-surface-3 border border-border-strong group-hover:border-accent group-hover:bg-accent transition-colors" />
                        <div className="absolute -left-[1px] top-6 bottom-0 w-[1px] bg-border-base/50 -mb-6 last:hidden" />
                        
                        <div className="flex flex-col">
                            <div className="flex items-center justify-between">
                              <span className="font-mono text-micro uppercase tracking-widest text-txt-primary font-bold">
                                {entry.change_type.replace('_', ' ')}
                              </span>
                              <span className="font-mono text-micro text-txt-tertiary uppercase tracking-widest">
                                {new Date(entry.created_at).toLocaleString()}
                              </span>
                            </div>
                            {entry.change_reason && (
                                <p className="text-sm font-serif text-txt-secondary italic mt-1 leading-relaxed border-l-2 border-border-base/50 pl-2 ml-1">
                                  {entry.change_reason}
                                </p>
                            )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-micro font-mono text-txt-muted uppercase tracking-widest p-4 border border-dashed border-border-base text-center">
                    NO_REVISION_HISTORY
                  </div>
                )}
              </div>

            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function ThesesPage({ onBack }: { onBack: () => void }) {
  const { user } = useAuth();
  const { data, isLoading, error } = useTheses();
  const [editingThesis, setEditingThesis] = useState<Thesis | null>(null);
  const [showEditor, setShowEditor] = useState(false);

  if (!user) {
    return (
      <div className="flex h-[50vh] flex-col items-center justify-center p-6 text-center w-full max-w-lg mx-auto">
        <div className="mb-4 flex items-center justify-center h-16 w-16 border border-border-base bg-surface-2 rounded-sm rotate-45">
          <BookOpen className="h-6 w-6 text-txt-muted -rotate-45" />
        </div>
        <h2 className="text-sm font-mono font-bold tracking-widest uppercase text-txt-primary mb-2">AUTH_REQUIRED</h2>
        <p className="font-mono text-micro text-txt-muted uppercase tracking-widest mb-6 leading-relaxed">
          SECURE_ENCLAVE_LOCKED. SIGN_IN_TO_ACCESS_PRIVATE_THESIS_LOGS.
        </p>
        <Button 
          onClick={onBack} 
          variant="ghost"
          className="rounded-sm font-mono text-micro uppercase tracking-widest h-8 px-4 border border-border-base hover:bg-surface-2 text-txt-secondary"
        >
          RETURN_TO_DASHBOARD
        </Button>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6 px-4 md:px-8 py-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col gap-4 border-b border-border-strong pb-6 mb-6">
        <div 
          className="inline-flex items-center gap-2 text-txt-muted hover:text-accent cursor-pointer transition-colors w-fit group" 
          onClick={onBack}
        >
          <ArrowLeft className="h-3 w-3 group-hover:-translate-x-1 transition-transform" />
          <span className="text-micro font-mono uppercase tracking-widest font-bold">RTN_DASHBOARD</span>
        </div>
        
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-mono font-bold tracking-tighter text-txt-primary uppercase">THESIS_REPOSITORY</h1>
            <p className="text-micro font-mono text-txt-muted uppercase tracking-widest">
              MANAGED_CONVICTION_LOGS // KILL_CRITERIA_MONITORING
            </p>
          </div>
          
          <Button 
            onClick={onBack} 
            className="rounded-sm font-mono text-micro font-bold uppercase tracking-widest bg-accent text-canvas hover:bg-accent/90 h-8 px-4"
          >
            [+] NEW_ANALYSIS_RUN
          </Button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-sm border border-bear/30 bg-bear/10 p-4 text-bear font-mono text-micro uppercase tracking-widest">
          ERR_LOAD_FAILED: {error.message}
        </div>
      )}

      {/* Thesis List */}
      <div className="space-y-3">
        {isLoading ? (
          [1, 2, 3].map((i) => (
            <div key={i} className="h-32 w-full animate-pulse rounded-sm bg-surface-2 border border-border-base/50" />
          ))
        ) : data && data.theses.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-sm border border-dashed border-border-strong py-24 text-center bg-surface-1/50">
            <div className="mb-4 text-txt-muted/50">
                 <BookOpen className="h-8 w-8" />
            </div>
            <h3 className="text-sm font-mono font-bold tracking-widest uppercase text-txt-primary">NO_THESIS_LOGS_FOUND</h3>
            <p className="max-w-md text-micro font-mono text-txt-muted mt-2 mb-6 uppercase tracking-widest leading-relaxed">
              REPOSITORY_EMPTY. INITIATE_TICKER_ANALYSIS_TO_GENERATE_AND_STORE_CONVICTION_LOGS.
            </p>
            <Button 
              onClick={onBack}
              variant="ghost"
              className="rounded-sm font-mono text-micro font-bold uppercase tracking-widest border border-accent text-accent hover:bg-accent-dim h-8 px-6"
            >
              INITIATE_ANALYSIS
            </Button>
          </div>
        ) : (
          data?.theses.map((thesis) => (
            <ThesisCard
              key={thesis.id}
              thesis={thesis}
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
        ticker={editingThesis?.ticker || ''}
        existingThesis={editingThesis}
      />
    </div>
  );
}
