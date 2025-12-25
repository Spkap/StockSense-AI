import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Bell, CheckCheck, Clock } from 'lucide-react';
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
    // In a real app we'd get the current user ID
    // For now we'll just fetch all alerts for demo purposes or filtered if we had auth context
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
    // Poll every 30 seconds
    const interval = setInterval(fetchAlerts, 30000);
    return () => clearInterval(interval);
  }, [filter]);

  const markAsRead = async (id: string) => {
    await supabase.from('alert_history').update({ is_read: true }).eq('id', id);
    // Optimistic update
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
    <Card className="h-full border-border bg-card">
      <CardHeader className="border-b border-border pb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            <div>
              <CardTitle>Alerts Center</CardTitle>
              <CardDescription>Monitor your active thesis alerts</CardDescription>
            </div>
          </div>
          <div className="flex gap-2">
            <div className="flex rounded-md border border-border bg-muted p-1">
                <Button 
                    variant={filter === 'unread' ? 'secondary' : 'ghost'} 
                    size="sm" 
                    className="h-7 text-xs"
                    onClick={() => setFilter('unread')}
                >
                    Unread
                </Button>
                <Button 
                    variant={filter === 'all' ? 'secondary' : 'ghost'} 
                    size="sm" 
                    className="h-7 text-xs"
                    onClick={() => setFilter('all')}
                >
                    All
                </Button>
            </div>
            {alerts.length > 0 && filter === 'unread' && (
                <Button variant="outline" size="sm" className="h-9" onClick={markAllRead}>
                    <CheckCheck className="mr-2 h-3 w-3" /> Mark All Read
                </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-[600px] overflow-y-auto">
            {loading && alerts.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">Loading alerts...</div>
            ) : alerts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-muted-foreground">
                    <Bell className="h-12 w-12 opacity-20 mb-4" />
                    <p>No {filter === 'unread' ? 'new' : ''} alerts found.</p>
                </div>
            ) : (
                <ul className="divide-y divide-border">
                    {alerts.map(alert => (
                        <li key={alert.id} className={cn(
                            "group flex flex-col gap-2 p-4 transition-colors hover:bg-muted/50",
                            !alert.is_read && "bg-primary/5"
                        )}>
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-2">
                                    <Badge variant={alert.alert_type === 'kill_criteria' ? 'destructive' : 'default'}>
                                        {alert.ticker}
                                    </Badge>
                                    <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                                        {alert.alert_type.replace('_', ' ')}
                                    </span>
                                    <span className="flex items-center gap-1 text-xs text-muted-foreground ml-2">
                                        <Clock className="h-3 w-3" />
                                        {new Date(alert.created_at).toLocaleString()}
                                    </span>
                                </div>
                                {!alert.is_read && (
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                        onClick={() => markAsRead(alert.id)}
                                        title="Mark as read"
                                    >
                                        <CheckCheck className="h-4 w-4" />
                                    </Button>
                                )}
                            </div>
                            
                            <h4 className="font-semibold text-foreground">
                                {alert.message || (alert.data?.match_confidence ? 
                                    `Kill Criteria Triggered: ${alert.data.triggered_criteria} ({(alert.data.match_confidence * 100).toFixed(0)}% confidence)` : 
                                    "New Alert")}
                            </h4>
                            
                            {alert.data?.analysis_summary && (
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                    {alert.data.analysis_summary}
                                </p>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </div>
      </CardContent>
    </Card>
  );
}
