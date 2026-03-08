/**
 * ThesisEditor - Modal for creating/editing investment theses
 * Stage 3: User Belief System
 * 
 * Obsidian Terminal styled — monochrome, dense, mechanical.
 */

import { useState, useEffect } from 'react';
import { X, Save, Loader2, AlertTriangle } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from '../context/AuthContext';
import { useCreateThesis, useUpdateThesis } from '../api/theses';
import type { Thesis, CreateThesisRequest } from '../types/thesis';

interface ThesisEditorProps {
  isOpen: boolean;
  onClose: () => void;
  ticker: string;
  existingThesis?: Thesis | null;
}

const CONVICTION_LEVELS = [
  { value: 'low', label: 'LOW', description: 'Speculative' },
  { value: 'medium', label: 'MED', description: 'Reasonable' },
  { value: 'high', label: 'HIGH', description: 'Strong' },
] as const;

export default function ThesisEditor({ isOpen, onClose, ticker, existingThesis }: ThesisEditorProps) {
  const { user } = useAuth();
  const createThesis = useCreateThesis();
  const updateThesis = useUpdateThesis();

  const [thesisSummary, setThesisSummary] = useState('');
  const [convictionLevel, setConvictionLevel] = useState<'low' | 'medium' | 'high'>('medium');
  const [killCriteria, setKillCriteria] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Populate form if editing existing thesis
  useEffect(() => {
    if (existingThesis) {
      setThesisSummary(existingThesis.thesis_summary);
      setConvictionLevel(existingThesis.conviction_level);
      setKillCriteria(existingThesis.kill_criteria.join('\n'));
    } else {
      setThesisSummary('');
      setConvictionLevel('medium');
      setKillCriteria('');
    }
  }, [existingThesis, isOpen]);

  if (!isOpen) return null;

  if (!user) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <div className="w-full max-w-md mx-4 border border-border-base bg-surface-1 rounded-sm overflow-hidden">
          <div className="p-6 text-center">
            <AlertTriangle className="h-12 w-12 text-accent mx-auto mb-4" />
            <h3 className="text-lg font-mono font-bold text-txt-primary mb-2 uppercase tracking-wider">AUTH_REQUIRED</h3>
            <p className="text-micro font-mono text-txt-muted uppercase tracking-widest mb-4">
              Sign in required to save theses.
            </p>
            <Button variant="outline" onClick={onClose} className="font-mono text-micro uppercase tracking-widest border-border-base rounded-sm">
              [CLOSE]
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (thesisSummary.trim().length < 10) {
      setError('Please provide a more detailed thesis (at least 10 characters)');
      return;
    }

    const killCriteriaList = killCriteria
      .split('\n')
      .map(c => c.trim())
      .filter(c => c.length > 0);

    try {
      if (existingThesis) {
        await updateThesis.mutateAsync({
          thesisId: existingThesis.id,
          updates: {
            thesis_summary: thesisSummary.trim(),
            conviction_level: convictionLevel,
            kill_criteria: killCriteriaList,
            change_reason: 'Updated thesis',
          },
        });
      } else {
        const newThesis: CreateThesisRequest = {
          ticker: ticker.toUpperCase(),
          thesis_summary: thesisSummary.trim(),
          conviction_level: convictionLevel,
          kill_criteria: killCriteriaList,
        };
        await createThesis.mutateAsync(newThesis);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save thesis');
    }
  };

  const isLoading = createThesis.isPending || updateThesis.isPending;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-lg mx-4 border border-border-base bg-surface-1 rounded-sm max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="relative border-b border-border-base bg-surface-2 px-4 py-3">
          <button
            onClick={onClose}
            className="absolute right-3 top-3 p-1 rounded-sm text-txt-muted hover:text-txt-primary hover:bg-surface-3 transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
          <h2 className="text-sm font-mono font-bold tracking-widest uppercase text-txt-primary">
            {existingThesis ? 'EDIT' : 'CREATE'}_THESIS: {ticker}
          </h2>
          <p className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1">
            Record why you care about this asset
          </p>
        </div>

        {/* Form */}
        <div className="p-4 bg-canvas">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Thesis Summary */}
            <div className="space-y-2">
              <label className="text-micro font-mono font-bold uppercase tracking-widest text-txt-secondary">
                THESIS_SUMMARY
              </label>
              <textarea
                value={thesisSummary}
                onChange={(e) => setThesisSummary(e.target.value)}
                placeholder="I believe this company will... because..."
                required
                minLength={10}
                rows={4}
                className="w-full px-3 py-2 rounded-sm border border-border-base bg-surface-1 text-sm font-mono text-txt-primary placeholder:text-txt-muted/50 focus:outline-none focus:border-border-focus resize-none"
              />
            </div>

            {/* Conviction Level */}
            <div className="space-y-2">
              <label className="text-micro font-mono font-bold uppercase tracking-widest text-txt-secondary">
                CONVICTION_LEVEL
              </label>
              <div className="grid grid-cols-3 gap-2">
                {CONVICTION_LEVELS.map((level) => (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => setConvictionLevel(level.value)}
                    className={`p-3 rounded-sm border text-center transition-colors ${
                      convictionLevel === level.value
                        ? 'border-accent bg-accent/10 text-accent'
                        : 'border-border-base hover:border-border-strong bg-surface-1 text-txt-muted hover:text-txt-secondary'
                    }`}
                  >
                    <span className="block text-micro font-mono font-bold uppercase tracking-widest">{level.label}</span>
                    <span className="block text-micro font-mono text-txt-muted/70 mt-0.5 uppercase tracking-wider">
                      {level.description}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Kill Criteria */}
            <div className="space-y-2">
              <label className="text-micro font-mono font-bold uppercase tracking-widest text-txt-secondary">
                KILL_CRITERIA
              </label>
              <p className="text-micro font-mono text-txt-muted uppercase tracking-wider">
                What conditions would make you exit? One per line.
              </p>
              <textarea
                value={killCriteria}
                onChange={(e) => setKillCriteria(e.target.value)}
                placeholder="Revenue growth slows below 10%&#10;CEO leaves the company&#10;Major competitor enters market"
                rows={3}
                className="w-full px-3 py-2 rounded-sm border border-border-base bg-surface-1 text-sm font-mono text-txt-primary placeholder:text-txt-muted/50 focus:outline-none focus:border-border-focus resize-none"
              />
            </div>

            {/* Error */}
            {error && (
              <p className="text-micro font-mono font-bold tracking-widest text-kill uppercase">{error}</p>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <Button
                type="button"
                variant="ghost"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1 font-mono text-micro uppercase tracking-widest border border-border-base rounded-sm h-9 hover:bg-surface-2"
              >
                [CANCEL]
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="flex-1 gap-2 font-mono text-micro uppercase tracking-widest border border-accent bg-accent/10 text-accent hover:bg-accent/20 rounded-sm h-9"
              >
                {isLoading ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Save className="h-3 w-3" />
                )}
                {existingThesis ? '[UPDATE]' : '[SAVE]'}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
