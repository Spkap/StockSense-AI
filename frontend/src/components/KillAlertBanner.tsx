/**
 * KillAlertBanner - Premium alert display for triggered kill criteria
 * 
 * Stage 4: Kill Criteria Monitoring
 * Glassmorphism design with animated warning pulse and smooth transitions.
 */

import { AlertTriangle, X, CheckCircle, Eye, ShieldAlert, ArrowRight } from 'lucide-react';
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
    <div className="space-y-3">
      <AnimatePresence>
        {alerts.map((alert, index) => (
          <motion.div
            key={alert.id}
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ delay: index * 0.1, type: 'spring', stiffness: 200 }}
            className="relative overflow-hidden rounded-xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-orange-500/10 to-amber-500/10 backdrop-blur-sm"
          >
            {/* Animated warning pulse */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-amber-500/10 via-orange-500/20 to-amber-500/10"
              animate={{ opacity: [0.3, 0.6, 0.3] }}
              transition={{ duration: 2, repeat: Infinity }}
            />

            <div className="relative p-5">
              {/* Header */}
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4">
                  {/* Icon with animated ring */}
                  <div className="relative">
                    <motion.div
                      className="absolute inset-0 rounded-full bg-amber-500/30"
                      animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                    <div className="relative flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg shadow-amber-500/25">
                      <ShieldAlert className="h-6 w-6 text-white" />
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1">
                    <h4 className="text-lg font-semibold text-foreground">
                      Kill Criteria Alert
                    </h4>
                    <div className="mt-0.5 flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">
                        Match confidence:
                      </span>
                      <span className={`text-sm font-bold ${
                        alert.match_confidence >= 0.8 ? 'text-destructive' :
                        alert.match_confidence >= 0.6 ? 'text-amber-500' : 'text-muted-foreground'
                      }`}>
                        {Math.round(alert.match_confidence * 100)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Dismiss button */}
                {onDismiss && (
                  <button
                    onClick={() => onDismiss(alert.id)}
                    className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-background/50 hover:text-foreground"
                    title="Dismiss alert"
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>

              {/* Alert Details */}
              <div className="mt-4 space-y-3">
                {/* Criteria Box */}
                <div className="rounded-lg bg-background/60 p-4 backdrop-blur-sm">
                  <div className="mb-1 flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-amber-600 dark:text-amber-400">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Your Kill Criteria
                  </div>
                  <p className="text-sm font-medium text-foreground leading-relaxed">
                    "{alert.triggered_criteria}"
                  </p>
                </div>

                {/* Triggering Signal */}
                <div className="flex items-center gap-2">
                  <ArrowRight className="h-4 w-4 shrink-0 text-amber-500" />
                  <div className="flex-1 rounded-lg bg-background/40 px-4 py-3 backdrop-blur-sm">
                    <div className="mb-1 text-xs font-medium text-muted-foreground">
                      Signal from latest analysis
                    </div>
                    <p className="text-sm text-foreground">
                      "{alert.triggering_signal}"
                    </p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-5 flex flex-wrap gap-3">
                {onViewThesis && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => onViewThesis(alert.thesis_id)}
                    className="gap-2 border-amber-500/30 hover:border-amber-500/50 hover:bg-amber-500/10"
                  >
                    <Eye className="h-4 w-4" />
                    View Thesis
                  </Button>
                )}
                {onAcknowledge && (
                  <Button
                    size="sm"
                    onClick={() => onAcknowledge(alert.id)}
                    className="gap-2 bg-gradient-to-r from-amber-500 to-orange-600 text-white hover:from-amber-600 hover:to-orange-700"
                  >
                    <CheckCircle className="h-4 w-4" />
                    Acknowledge & Review
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

