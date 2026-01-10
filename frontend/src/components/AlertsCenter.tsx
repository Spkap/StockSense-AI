import { useState, useEffect } from 'react';
import { Bell, CheckCheck, Clock, ShieldAlert } from 'lucide-react';
import { Badge } from './ui/badge';
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
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight">Alerts</h2>
          <p className="text-sm text-muted-foreground">Monitor your active thesis alerts</p>
        </div>
        <div className="flex items-center gap-2">
            <div className="flex bg-secondary/50 p-1 rounded-full backdrop-blur-sm border border-border/40">
                <button 
                    onClick={() => setFilter('unread')}
                    className={cn(
                        "px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-300",
                        filter === 'unread' ? "bg-background shadow-sm text-foreground ring-1 ring-black/5 dark:ring-white/10" : "text-muted-foreground hover:text-foreground"
                    )}
                >
                    Unread
                </button>
                <button 
                    onClick={() => setFilter('all')}
                    className={cn(
                        "px-4 py-1.5 text-xs font-medium rounded-full transition-all duration-300",
                        filter === 'all' ? "bg-background shadow-sm text-foreground ring-1 ring-black/5 dark:ring-white/10" : "text-muted-foreground hover:text-foreground"
                    )}
                >
                    All
                </button>
            </div>
            {alerts.length > 0 && filter === 'unread' && (
                <Button 
                    variant="outline" 
                    size="sm" 
                    className="h-9 gap-2 text-xs"
                    onClick={markAllRead}
                >
                    <CheckCheck className="h-3 w-3" /> 
                    Mark All Read
                </Button>
            )}
        </div>
      </div>

      {/* Alerts Feed */}
      <div className="min-h-[400px]">
        {loading && alerts.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-muted-foreground">
                <div className="bg-background/50 p-4 rounded-full">
                    <Bell className="h-6 w-6 animate-pulse opacity-50" />
                </div>
            </div>
        ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/40 py-24 text-center">
                <div className="bg-background/50 p-4 rounded-full mb-4">
                     <Bell className="h-8 w-8 text-muted-foreground/30" />
                </div>
                <h3 className="text-sm font-medium">No alerts found</h3>
                <p className="text-xs text-muted-foreground mt-1">
                    {filter === 'unread' ? "You're all caught up!" : "No alert history available."}
                </p>
            </div>
        ) : (
            <div className="space-y-3">
                {alerts.map(alert => (
                    <div 
                        key={alert.id} 
                        className={cn(
                            "group relative flex flex-col gap-3 rounded-xl border p-5 transition-all duration-300",
                            alert.is_read 
                                ? "bg-card border-border/40 opacity-80" 
                                : "bg-background border-primary/10 shadow-sm ring-1 ring-primary/5"
                        )}
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                                {/* Ticker Badge */}
                                <div className={cn(
                                    "flex items-center justify-center h-10 w-10 rounded-full font-bold text-xs",
                                    alert.alert_type === 'kill_criteria' 
                                        ? "bg-destructive/10 text-destructive"
                                        : "bg-primary/10 text-primary"
                                )}>
                                    {alert.ticker.substring(0, 2)}
                                </div>
                                
                                <div>
                                    <div className="flex items-center gap-2">
                                        <h4 className="font-semibold text-foreground text-sm">
                                            {alert.ticker}
                                        </h4>
                                        <Badge variant="secondary" className="text-[10px] font-normal lowercase bg-secondary/50">
                                            {alert.alert_type.replace('_', ' ')}
                                        </Badge>
                                    </div>
                                    <div className="flex items-center gap-1.5 mt-0.5">
                                        <Clock className="h-3 w-3 text-muted-foreground/60" />
                                        <span className="text-xs text-muted-foreground/80">
                                            {new Date(alert.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {!alert.is_read && (
                                <button 
                                    onClick={() => markAsRead(alert.id)}
                                    className="p-2 rounded-full hover:bg-secondary/80 text-muted-foreground transition-colors group-hover:opacity-100 opacity-0"
                                    title="Mark as read"
                                >
                                    <CheckCheck className="h-4 w-4" />
                                </button>
                            )}
                        </div>
                        
                        <div className="ml-12.5 pl-0.5">
                            <h5 className="text-sm font-medium leading-normal mb-1">
                                {alert.message || (alert.data?.match_confidence ? 
                                    <span className="flex items-center gap-2">
                                        <ShieldAlert className="h-4 w-4 text-destructive" />
                                        Kill Criteria Triggered: <span className="text-destructive font-semibold">{alert.data.triggered_criteria}</span>
                                    </span> 
                                    : "New Alert")}
                            </h5>
                            
                            {alert.data?.analysis_summary && (
                                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-2 bg-muted/20 p-2 rounded-lg">
                                    "{alert.data.analysis_summary}"
                                </p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        )}
      </div>
    </div>
  );
}
