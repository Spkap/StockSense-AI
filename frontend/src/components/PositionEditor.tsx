import { useEffect, useState } from 'react';
import { BriefcaseBusiness, Loader2, X } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader } from './ui/card';
import { Input } from './ui/input';
import { useCreatePosition } from '../api/user';
import type { CreatePositionRequest, PositionType } from '../types/api';

interface PositionEditorProps {
  isOpen: boolean;
  onClose: () => void;
  initialTicker?: string | null;
}

const POSITION_TYPES: Array<{ value: PositionType; label: string }> = [
  { value: 'long', label: 'Long' },
  { value: 'short', label: 'Short' },
  { value: 'watching', label: 'Watching' },
];

export default function PositionEditor({ isOpen, onClose, initialTicker }: PositionEditorProps) {
  const createPosition = useCreatePosition();
  const [ticker, setTicker] = useState(initialTicker ?? '');
  const [positionType, setPositionType] = useState<PositionType>('watching');
  const [entryDate, setEntryDate] = useState('');
  const [entryPrice, setEntryPrice] = useState('');
  const [currentShares, setCurrentShares] = useState('');
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    setTicker((initialTicker ?? '').toUpperCase());
    setPositionType('watching');
    setEntryDate('');
    setEntryPrice('');
    setCurrentShares('');
    setNotes('');
    setError(null);
  }, [initialTicker, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    const normalizedTicker = ticker.trim().toUpperCase();
    if (!normalizedTicker) {
      setError('Ticker is required');
      return;
    }

    const payload: CreatePositionRequest = {
      ticker: normalizedTicker,
      position_type: positionType,
      notes: notes.trim() || undefined,
    };

    if (entryDate) payload.entry_date = entryDate;
    if (entryPrice) payload.entry_price = Number(entryPrice);
    if (currentShares) payload.current_shares = Number(currentShares);

    try {
      await createPosition.mutateAsync(payload);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save position');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="mx-4 w-full max-w-lg shadow-2xl">
        <CardHeader className="relative border-b border-border pb-3">
          <button
            onClick={onClose}
            className="absolute right-4 top-4 rounded-full p-1 transition-colors hover:bg-muted"
            aria-label="Close position editor"
          >
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary">
              <BriefcaseBusiness className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Track Position</h2>
              <p className="text-sm text-muted-foreground">Add or watch a ticker from your portfolio.</p>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Ticker</label>
                <Input
                  value={ticker}
                  onChange={(event) => setTicker(event.target.value.toUpperCase().replace(/[^A-Z]/g, '').slice(0, 5))}
                  placeholder="AAPL"
                  required
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Position Type</label>
                <select
                  value={positionType}
                  onChange={(event) => setPositionType(event.target.value as PositionType)}
                  className="flex h-12 w-full rounded-xl bg-secondary/80 px-4 py-2 text-base shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
                >
                  {POSITION_TYPES.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Entry Date</label>
                <Input type="date" value={entryDate} onChange={(event) => setEntryDate(event.target.value)} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Entry Price</label>
                <Input type="number" min="0" step="0.01" value={entryPrice} onChange={(event) => setEntryPrice(event.target.value)} placeholder="172.40" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">Shares</label>
                <Input type="number" min="0" step="0.01" value={currentShares} onChange={(event) => setCurrentShares(event.target.value)} placeholder="25" />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-foreground">Notes</label>
              <textarea
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                rows={4}
                placeholder="Why are you tracking this? Entry thesis, sizing notes, or reminders."
                className="w-full rounded-xl bg-secondary/80 px-4 py-3 text-sm shadow-sm transition-all hover:bg-secondary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <div className="flex gap-2 pt-2">
              <Button type="button" variant="outline" onClick={onClose} className="flex-1" disabled={createPosition.isPending}>
                Cancel
              </Button>
              <Button type="submit" className="flex-1" disabled={createPosition.isPending}>
                {createPosition.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Save Position'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
