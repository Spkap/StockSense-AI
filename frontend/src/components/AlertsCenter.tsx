import { useState, useEffect } from 'react';
import { Bell, CheckSquare, Clock, ShieldAlert } from 'lucide-react';
import { Button } from './ui/button';
import { supabase } from '../utils/supabase';
import { cn } from '../utils/cn';

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
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('unread');

  const fetchAlerts = async () => {
    setLoading(true);
    const { data: { user } } = await supabase.auth.getUser();
    
    if (!user) {
        setLoading(false);
        return;
    }

    let query = supabase
      .from('alert_history')
      .select('*')
      .eq('user_id', user.id)
      .order('created_at', { ascending: false });

    if (filter === 'unread') {
      query = query.eq('is_read', false);
    }
    
    const { data } = await query;
    if (data) setAlerts(data);
    setLoading(false);
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const markAsRead = async (id: string) => {
    await supabase.from('alert_history').update({ is_read: true }).eq('id', id);
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, is_read: true } : a));
    if (filter === 'unread') {
        setAlerts(prev => prev.filter(a => a.id !== id));
    }
  };

  const markAllRead = async () => {
    const { data: { user } } = await supabase.auth.getUser();
    if (user) {
        await supabase.from('alert_history').update({ is_read: true }).eq('user_id', user.id);
        fetchAlerts();
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Minimal Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between border-b border-border-base pb-4 gap-4">
        <div>
          <h2 className="text-2xl font-mono font-bold tracking-tight text-txt-primary">SYS_ALERTS</h2>
          <p className="text-micro font-mono text-txt-muted uppercase tracking-widest mt-1">Monitor active monitoring signals</p>
        </div>
        <div className="flex items-center gap-4">
            <div className="flex bg-surface-1 border border-border-base p-0.5 rounded-sm">
                <button 
                    onClick={() => setFilter('unread')}
                    className={cn(
                        "px-4 py-1.5 text-micro font-mono uppercase tracking-widest transition-colors rounded-sm",
                        filter === 'unread' ? "bg-surface-3 text-txt-primary" : "text-txt-muted hover:text-txt-secondary hover:bg-surface-2"
                    )}
                >
                    UNREAD
                </button>
                <button 
                    onClick={() => setFilter('all')}
                    className={cn(
                        "px-4 py-1.5 text-micro font-mono uppercase tracking-widest transition-colors rounded-sm",
                        filter === 'all' ? "bg-surface-3 text-txt-primary" : "text-txt-muted hover:text-txt-secondary hover:bg-surface-2"
                    )}
                >
                    ALL_LOGS
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
                    ACK_ALL
                </Button>
            )}
        </div>
      </div>

      {/* Alerts Feed */}
      <div className="min-h-[400px] border border-border-base bg-surface-1 rounded-sm">
        {loading && alerts.length === 0 ? (
            <div className="flex flex-col h-64 items-center justify-center text-txt-muted opacity-50">
                <Bell className="h-4 w-4 animate-pulse opacity-50 mb-3 text-accent" />
                <span className="text-micro font-mono uppercase tracking-widest animate-pulse">POLLING_LOGS...</span>
            </div>
        ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center opacity-70">
                 <Bell className="h-6 w-6 text-txt-muted/50 mb-4" />
                <h3 className="text-sm font-mono text-txt-secondary tracking-widest uppercase">LOG_EMPTY</h3>
                <p className="text-micro font-mono text-txt-muted mt-2 tracking-wider uppercase">
                    {filter === 'unread' ? "NO_PENDING_ALERTS" : "NO_HISTORICAL_DATA"}
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
                        <div className="flex-1 flex flex-col justify-center">
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
                                    ACK
                                </button>
                            )}
                        </div>
                    </div>
                )})}
            </div>
        )}
      </div>
    </div>
  );
}
