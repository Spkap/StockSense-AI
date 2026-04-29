/**
 * ThesisEditor - Modal for creating/editing investment theses
 * Stage 3: User Belief System
 */

import { useState, useEffect } from 'react';
import { X, Save, Loader2, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Button } from './ui/button';
import { useAuth } from '../context/AuthContext';
import { useCreateThesis, useUpdateThesis } from '../api/theses';
import { usePositions } from '../api/user';
import type { Thesis, CreateThesisRequest } from '../types/thesis';
import type { AnalysisData } from '../types/api';

interface ThesisEditorProps {
  isOpen: boolean;
  onClose: () => void;
  ticker: string;
  existingThesis?: Thesis | null;
  analysisData?: AnalysisData | null;
}

const CONVICTION_LEVELS = [
  { value: 'low', label: 'Low', description: 'Speculative or uncertain' },
  { value: 'medium', label: 'Medium', description: 'Reasonable confidence' },
  { value: 'high', label: 'High', description: 'Strong conviction' },
] as const;

const TIME_HORIZONS = [
  { value: 'short', label: 'Short', description: '< 12 months' },
  { value: 'medium', label: 'Medium', description: '1-3 years' },
  { value: 'long', label: 'Long', description: '3+ years' },
] as const;

const THESIS_TYPES = [
  { value: 'growth', label: 'Growth' },
  { value: 'value', label: 'Value' },
  { value: 'income', label: 'Income' },
  { value: 'turnaround', label: 'Turnaround' },
  { value: 'special_situation', label: 'Special Situation' },
] as const;

const THESIS_STATUSES = [
  { value: 'active', label: 'Active' },
  { value: 'validated', label: 'Validated' },
  { value: 'invalidated', label: 'Invalidated' },
  { value: 'exited', label: 'Exited' },
] as const;

export default function ThesisEditor({ isOpen, onClose, ticker, existingThesis, analysisData }: ThesisEditorProps) {
  const { user } = useAuth();
  const createThesis = useCreateThesis();
  const updateThesis = useUpdateThesis();
  const { data: positionsData } = usePositions(isOpen && !!user);

  const [thesisSummary, setThesisSummary] = useState('');
  const [convictionLevel, setConvictionLevel] = useState<'low' | 'medium' | 'high'>('medium');
  const [killCriteria, setKillCriteria] = useState('');
  const [timeHorizon, setTimeHorizon] = useState<'short' | 'medium' | 'long'>('medium');
  const [thesisType, setThesisType] = useState<'growth' | 'value' | 'income' | 'turnaround' | 'special_situation'>('growth');
  const [status, setStatus] = useState<'active' | 'validated' | 'invalidated' | 'exited'>('active');
  const [positionId, setPositionId] = useState('');
  const [changeReason, setChangeReason] = useState('');
  const [invalidationReason, setInvalidationReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  const matchingPositions = (positionsData?.positions ?? []).filter((position) => position.ticker === ticker.toUpperCase());

  // Populate form if editing existing thesis
  useEffect(() => {
    if (existingThesis) {
      setThesisSummary(existingThesis.thesis_summary);
      setConvictionLevel(existingThesis.conviction_level);
      setKillCriteria(existingThesis.kill_criteria.join('\n'));
      setTimeHorizon(existingThesis.time_horizon);
      setThesisType(existingThesis.thesis_type);
      setStatus(existingThesis.status);
      setPositionId(existingThesis.position_id ?? '');
      setChangeReason('');
      setInvalidationReason('');
    } else {
      setThesisSummary('');
      setConvictionLevel('medium');
      setKillCriteria('');
      setTimeHorizon('medium');
      setThesisType('growth');
      setStatus('active');
      setPositionId('');
      setChangeReason('');
      setInvalidationReason('');
    }
  }, [existingThesis, isOpen]);

  if (!isOpen) return null;

  if (!user) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
        <Card className="w-full max-w-md mx-4 shadow-2xl">
          <CardContent className="p-6 text-center">
            <AlertTriangle className="h-12 w-12 text-warning mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Sign in Required</h3>
            <p className="text-sm text-muted-foreground mb-4">
              You need to sign in to save investment theses.
            </p>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const buildOriginSnapshot = () => {
    if (!analysisData) return undefined;
    return {
      sentiment: analysisData.overall_sentiment || analysisData.sentiment_report || '',
      confidence: analysisData.overall_confidence ?? 0,
      skeptic_verdict: analysisData.skeptic_sentiment || undefined,
      key_themes: (analysisData.key_themes ?? []).map((theme) => theme.theme),
      timestamp: analysisData.timestamp,
    };
  };

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
            status,
            invalidation_reason: invalidationReason.trim() || undefined,
            change_reason: changeReason.trim() || 'Updated thesis',
          },
        });
      } else {
        const newThesis: CreateThesisRequest = {
          ticker: ticker.toUpperCase(),
          thesis_summary: thesisSummary.trim(),
          conviction_level: convictionLevel,
          kill_criteria: killCriteriaList,
          time_horizon: timeHorizon,
          thesis_type: thesisType,
          position_id: positionId || undefined,
          origin_analysis_id: analysisData?.id,
          origin_analysis_snapshot: buildOriginSnapshot(),
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
      <Card className="w-full max-w-lg mx-4 shadow-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="relative pb-2 border-b border-border">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 p-1 rounded-full hover:bg-muted transition-colors"
          >
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
          <h2 className="text-xl font-bold">
            {existingThesis ? 'Edit' : 'Create'} Thesis: {ticker}
          </h2>
          <p className="text-sm text-muted-foreground">
            Record why you care about this asset
          </p>
        </CardHeader>

        <CardContent className="pt-4">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Thesis Summary */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Why do you care about {ticker}?
              </label>
              <textarea
                value={thesisSummary}
                onChange={(e) => setThesisSummary(e.target.value)}
                placeholder="I believe this company will... because..."
                required
                minLength={10}
                rows={4}
                className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none"
              />
            </div>

            {/* Conviction Level */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Conviction Level
              </label>
              <div className="grid gap-2 sm:grid-cols-3">
                {CONVICTION_LEVELS.map((level) => (
                  <button
                    key={level.value}
                    type="button"
                    onClick={() => setConvictionLevel(level.value)}
                    className={`p-3 rounded-lg border text-center transition-colors ${
                      convictionLevel === level.value
                        ? 'border-primary bg-primary/10 text-primary'
                        : 'border-border hover:border-muted-foreground'
                    }`}
                  >
                    <span className="block text-sm font-medium">{level.label}</span>
                    <span className="block text-xs text-muted-foreground mt-0.5">
                      {level.description}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            {/* Kill Criteria */}
            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">
                Kill Criteria (one per line)
              </label>
              <p className="text-xs text-muted-foreground">
                What conditions would make you exit this position?
              </p>
              <textarea
                value={killCriteria}
                onChange={(e) => setKillCriteria(e.target.value)}
                placeholder="Revenue growth slows below 10%&#10;CEO leaves the company&#10;Major competitor enters market"
                rows={3}
                className="w-full px-3 py-2 rounded-lg border border-input bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring resize-none font-mono text-sm"
              />
            </div>

            {!existingThesis && (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Time Horizon</label>
                  <select
                    value={timeHorizon}
                    onChange={(event) => setTimeHorizon(event.target.value as typeof timeHorizon)}
                    className="flex h-12 w-full rounded-lg bg-secondary/80 px-4 py-2 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                  >
                    {TIME_HORIZONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label} · {option.description}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">Thesis Type</label>
                  <select
                    value={thesisType}
                    onChange={(event) => setThesisType(event.target.value as typeof thesisType)}
                    className="flex h-12 w-full rounded-lg bg-secondary/80 px-4 py-2 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                  >
                    {THESIS_TYPES.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            )}

            {!existingThesis && matchingPositions.length > 0 && (
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Link to Position</label>
                <select
                  value={positionId}
                  onChange={(event) => setPositionId(event.target.value)}
                  className="flex h-12 w-full rounded-lg bg-secondary/80 px-4 py-2 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                >
                  <option value="">No linked position</option>
                  {matchingPositions.map((position) => (
                    <option key={position.id} value={position.id}>
                      {position.position_type.toUpperCase()} · {position.ticker}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {existingThesis && (
              <>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Status</label>
                    <select
                      value={status}
                      onChange={(event) => setStatus(event.target.value as typeof status)}
                      className="flex h-12 w-full rounded-lg bg-secondary/80 px-4 py-2 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                    >
                      {THESIS_STATUSES.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Change Reason</label>
                    <input
                      value={changeReason}
                      onChange={(event) => setChangeReason(event.target.value)}
                      placeholder="What changed in your thesis?"
                      className="flex h-12 w-full rounded-lg bg-secondary/80 px-4 py-2 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                    />
                  </div>
                </div>

                {(status === 'invalidated' || status === 'exited') && (
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground">Invalidation / Exit Reason</label>
                    <textarea
                      value={invalidationReason}
                      onChange={(event) => setInvalidationReason(event.target.value)}
                      rows={3}
                      placeholder="What specifically invalidated the thesis or triggered the exit?"
                      className="w-full rounded-lg bg-secondary/80 px-4 py-3 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                    />
                  </div>
                )}
              </>
            )}

            {!existingThesis && analysisData && (
              <div className="rounded-xl border border-primary/15 bg-primary/5 p-4 text-sm text-muted-foreground">
                This thesis will be linked to the current analysis snapshot so you can compare what changed later.
              </div>
            )}

            {/* Error */}
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}

            {/* Actions */}
            <div className="grid gap-2 pt-2 sm:flex">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                disabled={isLoading}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={isLoading}
                className="flex-1 gap-2"
              >
                {isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                {existingThesis ? 'Update' : 'Save'} Thesis
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
