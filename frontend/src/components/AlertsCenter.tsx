import { useState, useEffect } from 'react';
import { Bell, CheckSquare, Clock, ShieldAlert } from 'lucide-react';
import { Button } from './ui/button';
import { supabase } from '../utils/supabase';
import { cn } from '../utils/cn';
import { useAuth } from '../context/AuthContext';

interface Alert {
  id: string;
  user_id: string;
  thesis_id: string;
  ticker: string;
  alert_type: string;
  message: string;
  data: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export default function AlertsCenter() {
  const { user, loading: authLoading } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [alertLimit, setAlertLimit] = useState(25);
  const [filter, setFilter] = useState<'all' | 'unread'>('unread');

  const fetchAlerts = async () => {
    if (!supabase || !user) { setAlerts([]); setLoading(false); return; }
    setError(null);
    setLoading(true);

    let query = supabase
      .from('alert_history')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false })
      .limit(alertLimit);

    if (filter === 'unread') {
      query = query.eq('is_read', false);
    }
    
    const { data, error: fetchError } = await query;
    if (fetchError) setError('Could not load alerts. Please try again.');
    if (data) setAlerts(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [filter, user?.id, alertLimit]);

  const markAsRead = async (id: string) => {
    if (!supabase || !user) return;
    const { data: updated, error: updateError } = await supabase.from('alert_history').update({ is_read: true, status: 'acknowledged' }).eq('id', id).eq('user_id', user.id).select('id');
    if (updateError || !updated?.length) { setError('Could not update the alert. Please try again.'); return; }
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
    if (filter === 'unread') {
        setAlerts(prev => prev.filter(a => a.id !== id));
    }
  };

  const markAllRead = async () => {
    if (!supabase || !user) return;
    const { error: updateError } = await supabase.from('alert_history').update({ is_read: true, status: 'acknowledged' }).eq('user_id', user.id).eq('is_read', false);
    if (updateError) { setError('Could not update alerts. Please try again.'); return; }
    await fetchAlerts();
  };

  if (authLoading) return <p role="status" className="p-8 text-txt-secondary">Checking your session…</p>;
  if (!user) return <div className="p-8 text-center space-y-3"><h2 className="text-xl text-txt-primary">Sign in to view alerts</h2><p className="text-sm text-txt-secondary">Use the sign-in button above to access your thesis monitoring and alerts.</p></div>;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Minimal Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-border-base pb-4 gap-4">
        <div>
          <h2 className="text-2xl font-mono font-bold tracking-tight text-txt-primary">Alerts</h2>
          <p className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1">Thesis monitoring and review signals</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
            <div className="flex flex-wrap bg-surface-1 border border-border-base p-0.5 rounded-sm">
                <button 
                    onClick={() => { setFilter('unread'); setAlertLimit(25); }}
                    className={cn(
                        "px-3 py-2 text-micro font-mono uppercase tracking-widest transition-colors rounded-sm",
                        filter === 'unread' ? "bg-surface-3 text-txt-primary" : "text-txt-muted hover:text-txt-secondary hover:bg-surface-2"
                    )}
                >
                    UNREAD
                </button>
                <button 
                    onClick={() => { setFilter('all'); setAlertLimit(25); }}
                    className={cn(
                        "px-3 py-2 text-micro font-mono uppercase tracking-widest transition-colors rounded-sm",
                        filter === 'all' ? "bg-surface-3 text-txt-primary" : "text-txt-muted hover:text-txt-secondary hover:bg-surface-2"
                    )}
                >
                    All alerts
                </button>
            </div>
            {alerts.length > 0 && filter === 'unread' && (
                <Button 
                    variant="ghost" 
                    size="sm" 
                    className="h-8 gap-2 text-micro font-mono uppercase tracking-widest border border-border-base rounded-sm hover:bg-surface-2"
                    onClick={markAllRead}
                >
                    <CheckSquare className="h-3 w-3" /> 
                    Mark all read
                </Button>
            )}
        </div>
      </div>

      {error && <div role="alert" className="p-4 border border-bear text-bear">{error}<button onClick={fetchAlerts} className="ml-3 underline">Refresh alerts</button></div>}
      <p className="text-sm text-txt-secondary">Showing the latest {alerts.length} {filter === 'unread' ? 'unread ' : ''}alerts.</p>
      {/* Alerts Feed */}
      <div className="min-h-[400px] border border-border-base bg-surface-1 rounded-sm">
        {loading && alerts.length === 0 ? (
            <div className="flex flex-col h-64 items-center justify-center text-txt-muted opacity-50">
                <Bell className="h-4 w-4 animate-pulse opacity-50 mb-3 text-accent" />
                <span className="text-micro font-mono uppercase tracking-widest animate-pulse">Loading alerts…</span>
            </div>
        ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center opacity-70">
                 <Bell className="h-6 w-6 text-txt-muted/50 mb-4" />
                <h3 className="text-sm font-mono text-txt-secondary tracking-widest uppercase">You’re all caught up</h3>
                <p className="text-micro font-mono text-txt-muted mt-2 tracking-wider uppercase">
                    {filter === 'unread' ? "No unread alerts" : "No alert history"}
                </p>
            </div>
        ) : (
            <div className="flex flex-col">
                {alerts.map((alert, idx) => {
                    const isKill = alert.alert_type === 'kill_criteria';
                    return (
                    <div 
                        key={alert.id} 
                        className={cn(
                            "group relative flex flex-col md:flex-row gap-4 p-4 transition-colors",
                            idx !== 0 && "border-t border-border-base",
                            alert.is_read 
                                ? "bg-surface-1 opacity-80 hover:bg-surface-2/50" 
                                : isKill ? "bg-kill/5 hover:bg-kill/10" : "bg-surface-2 hover:bg-surface-3"
                        )}
                    >
                        {/* Indicator Bar for Unread */}
                        {!alert.is_read && (
                            <div className={cn("absolute left-0 top-0 bottom-0 w-0.5", isKill ? "bg-kill" : "bg-accent")} />
                        )}

                        {/* Metadata Column */}
                        <div className="flex flex-col gap-1 min-w-[140px] shrink-0">
                            <div className="flex items-center gap-2">
                                <span className={cn("text-sm font-mono font-bold tracking-tight", isKill ? "text-kill" : "text-txt-primary")}>{alert.ticker}</span>
                            </div>
                            <span className={cn(
                                "text-micro font-mono uppercase tracking-widest",
                                isKill ? "text-kill/80" : "text-txt-muted"
                            )}>
                                {alert.alert_type.replace('_', ' ')}
                            </span>
                            <div className="flex items-center gap-1 mt-1 text-txt-muted/70">
                                <Clock className="h-3 w-3" />
                                <span className="text-micro font-mono tracking-wider">
                                    {new Date(alert.created_at).toLocaleString(undefined, {
                                        month: 'numeric', day: 'numeric', hour: '2-digit', minute:'2-digit'
                                    })}
                                </span>
                            </div>
                        </div>

                        {/* Alert Content */}
                        <div className="min-w-0 flex-1 flex flex-col justify-center">
                            <h5 className="text-sm font-mono text-txt-primary leading-relaxed mb-1.5 flex items-center gap-2">
                                {isKill && <ShieldAlert className="h-4 w-4 text-kill shrink-0" />}
                                {alert.message || (alert.data?.match_confidence && isKill ? 
                                    <span className="flex items-center gap-2">
                                        KILL_TRIGGER: <span className="text-kill font-bold">{alert.data.triggered_criteria}</span>
                                    </span> 
                                    : "SYS_SIGNAL_DETECTED")}
                            </h5>
                            
                            {alert.data?.analysis_summary && (
                                <p className="text-sm font-serif text-txt-secondary leading-relaxed line-clamp-2 pl-3 border-l-2 border-border-strong mt-1 italic opacity-80">
                                    "{alert.data.analysis_summary}"
                                </p>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center md:items-start justify-end shrink-0 pl-2">
                            {!alert.is_read && (
                                <button 
                                    onClick={() => markAsRead(alert.id)}
                                    className="px-2 py-1 flex items-center gap-1.5 rounded-sm bg-surface-3 text-micro font-mono uppercase tracking-widest text-txt-secondary hover:text-txt-primary hover:bg-border-strong transition-colors"
                                    title="Mark as read"
                                >
                                    <CheckSquare className="h-3 w-3" />
                                    Mark read
                                </button>
                            )}
                        </div>
                    </div>
                )})}
            </div>
        )}
      </div>
      {alerts.length >= alertLimit && <Button variant="outline" disabled={loading} onClick={() => setAlertLimit(limit => limit + 25)}>Load older alerts</Button>}
    </div>
  );
}
