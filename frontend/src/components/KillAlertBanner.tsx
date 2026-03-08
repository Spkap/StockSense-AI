/**
 * KillAlertBanner - Premium alert display for triggered kill criteria
 * 
 * Stage 4: Kill Criteria Monitoring
 * Stark Obsidian Terminal design with high-contrast warning elements
 */

import { X, ShieldAlert } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './ui/button';
import type { KillAlert } from '../types/api';

interface KillAlertBannerProps {
  alerts: KillAlert[];
  onDismiss?: (alertId: string) => void;
  onAcknowledge?: (alertId: string) => void;
  onViewThesis?: (thesisId: string) => void;
}

export default function KillAlertBanner({ 
  alerts, 
  onDismiss, 
  onAcknowledge,
  onViewThesis 
}: KillAlertBannerProps) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <AnimatePresence>
        {alerts.map((alert, index) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ delay: index * 0.1, duration: 0.3 }}
            className="flex flex-col border-l-4 border-kill border-y border-r border-y-border-base border-r-border-base bg-kill-dim rounded-none w-full overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-kill/20 px-4 py-3 bg-kill/5">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center p-1 bg-kill/10 rounded-none border border-kill/30">
                  <ShieldAlert className="h-4 w-4 text-kill animate-pulse" />
                </div>
                <div className="flex flex-col">
                  <h4 className="text-micro font-mono font-bold tracking-widest text-kill uppercase leading-none">
                    KILL_CRITERIA_TRIGGERED
                  </h4>
                  <span className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1">
                    SYS_ALERT // HIGH_PRIORITY
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-4">
                <div className="hidden sm:flex flex-col items-end">
                  <span className="text-sm font-mono font-bold text-kill leading-none tracking-tight">
                    {Math.round(alert.match_confidence * 100)}%
                  </span>
                  <span className="text-micro font-mono text-kill/70 uppercase tracking-widest mt-1">
                    MATCH_CONF
                  </span>
                </div>
                
                {onDismiss && (
                  <button
                    onClick={() => onDismiss(alert.id)}
                    className="p-1.5 text-txt-muted hover:text-kill hover:bg-kill/10 border border-transparent hover:border-kill/30 transition-colors rounded-none ml-2"
                    title="Dismiss alert"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
            </div>

            {/* Content Body */}
            <div className="p-4 flex flex-col gap-4 bg-canvas/50">
              <div className="flex flex-col lg:flex-row gap-4">
                
                {/* Criteria Definition */}
                <div className="flex-1 flex flex-col gap-2 p-3 border border-border-base bg-surface-1 rounded-none">
                  <div className="flex items-center gap-2 border-b border-border-base/50 pb-2 mb-1">
                    <span className="text-micro font-mono text-txt-muted uppercase tracking-widest font-bold">CRITERIA_DEF</span>
                  </div>
                  <p className="text-sm font-serif text-txt-primary leading-relaxed border-l-2 border-accent pl-3">
                    {alert.triggered_criteria}
                  </p>
                </div>

                {/* Triggering Signal */}
                <div className="flex-1 flex flex-col gap-2 p-3 border border-kill/30 bg-kill/5 rounded-none">
                  <div className="flex items-center gap-2 border-b border-kill/20 pb-2 mb-1">
                    <span className="text-micro font-mono text-kill uppercase tracking-widest font-bold">TRIGGERING_SIGNAL</span>
                  </div>
                  <p className="text-sm font-serif text-txt-primary leading-relaxed border-l-2 border-kill pl-3">
                    {alert.triggering_signal}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 justify-end pt-2">
                {onViewThesis && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onViewThesis(alert.thesis_id)}
                    className="h-8 gap-2 font-mono text-micro uppercase tracking-widest font-bold text-txt-secondary border border-border-base hover:bg-surface-2 hover:text-txt-primary rounded-none px-4"
                  >
                    [VIEW_THESIS]
                  </Button>
                )}
                {onAcknowledge && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onAcknowledge(alert.id)}
                    className="h-8 gap-2 font-mono text-micro uppercase tracking-widest font-bold text-kill border border-kill/50 bg-kill/10 hover:bg-kill/20 rounded-none px-4"
                  >
                    [ACKNOWLEDGE]
                  </Button>
                )}
              </div>
            </div>
            
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

