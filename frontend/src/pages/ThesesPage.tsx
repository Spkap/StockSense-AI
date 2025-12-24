/**
 * ThesesPage - List of user's investment theses
 * Stage 3: User Belief System
 */

import { useState } from 'react';
import { BookOpen, ChevronDown, ChevronRight, Clock, AlertTriangle, Target } from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { useAuth } from '../context/AuthContext';
import { useTheses, useThesisHistory } from '../api/theses';
import ThesisEditor from '../components/ThesisEditor';
import type { Thesis } from '../types/thesis';

const CONVICTION_COLORS = {
  low: 'bg-muted text-muted-foreground',
  medium: 'bg-warning/20 text-warning',
  high: 'bg-success/20 text-success',
};

const STATUS_LABELS = {
  active: { label: 'Active', color: 'bg-primary/20 text-primary' },
  validated: { label: 'Validated', color: 'bg-success/20 text-success' },
  invalidated: { label: 'Invalidated', color: 'bg-destructive/20 text-destructive' },
  exited: { label: 'Exited', color: 'bg-muted text-muted-foreground' },
};

function ThesisCard({ thesis, onEdit }: { thesis: Thesis; onEdit: () => void }) {
  const [expanded, setExpanded] = useState(false);
  const { data: historyData } = useThesisHistory(expanded ? thesis.id : null);

  const statusConfig = STATUS_LABELS[thesis.status] || STATUS_LABELS.active;

  return (
    <Card className="overflow-hidden">
      <CardContent className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 hover:bg-muted rounded transition-colors"
            >
              {expanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
            <div>
              <h3 className="text-lg font-bold">{thesis.ticker}</h3>
              <p className="text-xs text-muted-foreground">
                <Clock className="h-3 w-3 inline mr-1" />
                Updated {new Date(thesis.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={CONVICTION_COLORS[thesis.conviction_level]}>
              {thesis.conviction_level}
            </Badge>
            <Badge className={statusConfig.color}>
              {statusConfig.label}
            </Badge>
          </div>
        </div>

        {/* Summary */}
        <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
          {thesis.thesis_summary}
        </p>

        {/* Expanded Content */}
        {expanded && (
          <div className="mt-4 pt-4 border-t border-border space-y-4">
            {/* Kill Criteria */}
            {thesis.kill_criteria.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
                  <Target className="h-3 w-3" />
                  Kill Criteria
                </h4>
                <ul className="space-y-1">
                  {thesis.kill_criteria.map((criteria, i) => (
                    <li key={i} className="text-sm flex items-start gap-2">
                      <AlertTriangle className="h-3 w-3 text-warning mt-0.5 shrink-0" />
                      <span>{criteria}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* History */}
            {historyData && historyData.history.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  History
                </h4>
                <div className="space-y-2">
                  {historyData.history.slice(0, 5).map((entry) => (
                    <div key={entry.id} className="text-xs text-muted-foreground">
                      <span className="font-medium">{new Date(entry.created_at).toLocaleDateString()}</span>
                      {' — '}
                      <span>{entry.change_type.replace('_', ' ')}</span>
                      {entry.change_reason && (
                        <span className="text-foreground"> ({entry.change_reason})</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Edit Button */}
            <Button variant="outline" size="sm" onClick={onEdit}>
              Edit Thesis
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ThesesPage({ onBack }: { onBack: () => void }) {
  const { user } = useAuth();
  const { data, isLoading, error } = useTheses();
  const [editingThesis, setEditingThesis] = useState<Thesis | null>(null);
  const [showEditor, setShowEditor] = useState(false);

  if (!user) {
    return (
      <div className="p-6">
        <Card className="max-w-md mx-auto">
          <CardContent className="p-6 text-center">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h2 className="text-lg font-semibold mb-2">Sign in to view theses</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Your investment theses are private and require authentication.
            </p>
            <Button variant="outline" onClick={onBack}>
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 lg:p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Button variant="ghost" onClick={onBack} className="mb-2 -ml-2">
            ← Back to Dashboard
          </Button>
          <h1 className="text-2xl font-bold">My Theses</h1>
          <p className="text-sm text-muted-foreground">
            Track your investment beliefs and kill criteria
          </p>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <Card className="mb-6 border-destructive/50 bg-destructive/10">
          <CardContent className="p-4 text-destructive">
            Failed to load theses: {error.message}
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-4">
                <div className="h-6 w-20 bg-muted animate-pulse rounded mb-2" />
                <div className="h-4 w-full bg-muted animate-pulse rounded" />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && data && data.theses.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No theses yet</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Analyze a stock and save your investment thesis to get started.
            </p>
            <Button onClick={onBack}>
              Analyze a Stock
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Thesis List */}
      {!isLoading && data && data.theses.length > 0 && (
        <div className="space-y-4">
          {data.theses.map((thesis) => (
            <ThesisCard
              key={thesis.id}
              thesis={thesis}
              onEdit={() => {
                setEditingThesis(thesis);
                setShowEditor(true);
              }}
            />
          ))}
        </div>
      )}

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
