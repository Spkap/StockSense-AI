import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import TickerInput, { TickerInputRef } from './components/TickerInput';
import QuickSelect from './components/QuickSelect';
import AnalysisHistory from './components/AnalysisHistory';
import ResultsTabs from './components/ResultsTabs';
import StreamingAnalysisProgress from './components/StreamingAnalysisProgress';
import KillAlertBanner from './components/KillAlertBanner';
import AlertsCenter from './components/AlertsCenter';
import EmptyState from './components/EmptyState';
import ErrorBoundary from './components/ErrorBoundary';
import ThesesPage from './pages/ThesesPage';
import { ThemeProvider } from './context/ThemeContext';
import { SidebarProvider, useSidebar } from './context/SidebarContext';
import { ToastProvider, useToast } from './components/ui/toast';
import { AuthProvider } from './context/AuthContext';
import { useAppKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useHealthCheck, useAnalysisResults, useKillAlerts } from './api/hooks';
import { useStreamingAnalysis } from './hooks/useStreamingAnalysis';
import type { AnalysisData, KillAlert } from './types/api';
import { AlertCircle } from 'lucide-react';
import { cn } from './utils/cn';

function normalizeAnalysisData(data: AnalysisData | null): AnalysisData | null {
  if (!data) return null;

  return {
    ...data,
    summary: typeof data.summary === 'string' ? data.summary : '',
    sentiment_report: typeof data.sentiment_report === 'string' ? data.sentiment_report : '',
    price_data: Array.isArray(data.price_data) ? data.price_data : [],
    headlines: Array.isArray(data.headlines) ? data.headlines : [],
    headlines_count:
      typeof data.headlines_count === 'number'
        ? data.headlines_count
        : Array.isArray(data.headlines)
          ? data.headlines.length
          : 0,
    reasoning_steps: Array.isArray(data.reasoning_steps) ? data.reasoning_steps : [],
    tools_used: Array.isArray(data.tools_used) ? data.tools_used : [],
    iterations: typeof data.iterations === 'number' ? data.iterations : 0,
    headline_analyses: Array.isArray(data.headline_analyses) ? data.headline_analyses : [],
    key_themes: Array.isArray(data.key_themes) ? data.key_themes : [],
    risks_identified: Array.isArray(data.risks_identified) ? data.risks_identified : [],
    information_gaps: Array.isArray(data.information_gaps) ? data.information_gaps : [],
    critiques: Array.isArray(data.critiques) ? data.critiques : [],
    bear_cases: Array.isArray(data.bear_cases) ? data.bear_cases : [],
    hidden_risks: Array.isArray(data.hidden_risks) ? data.hidden_risks : [],
    would_change_mind: Array.isArray(data.would_change_mind) ? data.would_change_mind : [],
    fundamental_data:
      data.fundamental_data && typeof data.fundamental_data === 'object'
        ? data.fundamental_data
        : undefined,
    source: data.source ?? 'react_analysis',
    agent_type: data.agent_type ?? 'ReAct',
    timestamp: typeof data.timestamp === 'string' ? data.timestamp : new Date().toISOString(),
  };
}

function AppContent() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'dashboard' | 'theses' | 'alerts'>('dashboard');
  const { isCollapsed } = useSidebar();
  const { addToast } = useToast();
  const tickerInputRef = useRef<TickerInputRef>(null);
  
  // Keyboard shortcuts (Cmd/Ctrl+K to focus search)
  useAppKeyboardShortcuts({
    onFocusSearch: () => tickerInputRef.current?.focus(),
  });
  
  // Health check
  const { data: health, isError: isHealthError } = useHealthCheck();
  const backendStatus = health?.status === 'ok' || health?.status === 'degraded' 
    ? 'online' 
    : isHealthError 
      ? 'offline' 
      : 'checking...';
  
  // Streaming Analysis (Stage 4)
  const streaming = useStreamingAnalysis();
  const [killAlerts, setKillAlerts] = useState<KillAlert[]>([]);
  const [alertTicker, setAlertTicker] = useState<string | null>(null);
  const { data: killAlertsData } = useKillAlerts(alertTicker);

  // Fetch cached results when ticker changes
  const { data: resultsData, refetch: refetchResults } = useAnalysisResults(
    selectedTicker,
    !streaming.isStreaming
  );
  
  // Use streaming final data or cached results
  const analysisData: AnalysisData | null = normalizeAnalysisData(
    streaming.finalData || resultsData?.data || null
  );

  const handleAnalyze = (ticker: string, _force: boolean = false) => {
    setSelectedTicker(ticker);
    setKillAlerts([]);
    setAlertTicker(null);
    streaming.startAnalysis(ticker);
  };

  const handleRefresh = () => {
    if (selectedTicker) {
      handleAnalyze(selectedTicker, true);
    }
  };

  const handleSelectHistory = (ticker: string) => {
    setSelectedTicker(ticker);
    streaming.reset();
  };

  const handleCancel = () => {
    streaming.stopAnalysis();
    setSelectedTicker(null);
    addToast({
      type: 'info',
      title: 'Analysis Cancelled',
      message: 'The analysis request has been cancelled.',
    });
  };

  // Refetch cached results when streaming completes
  useEffect(() => {
    if (streaming.finalData && selectedTicker) {
      refetchResults();
    }
  }, [streaming.finalData, selectedTicker, refetchResults]);

  // Fetch kill alerts after streaming completes (authenticated users)
  useEffect(() => {
    if (streaming.finalData && selectedTicker) {
      setAlertTicker(selectedTicker);
    }
  }, [streaming.finalData, selectedTicker]);

  // Populate killAlerts state when the query resolves
  useEffect(() => {
    if (killAlertsData && killAlertsData.length > 0) {
      setKillAlerts(killAlertsData);
    }
  }, [killAlertsData]);

  const isLoading = streaming.isStreaming;
  const error = streaming.error;

  // Show toast notification for errors
  useEffect(() => {
    if (error) {
      addToast({
        type: 'error',
        title: 'Analysis Failed',
        message: error,
        duration: 8000,
      });
    }
  }, [error, addToast]);

  // Show toast for successful streaming analysis
  useEffect(() => {
    if (streaming.finalData?.ticker) {
      addToast({
        type: 'success',
        title: 'Analysis Complete',
        message: `Successfully analyzed ${streaming.finalData.ticker}`,
      });
    }
  }, [streaming.finalData, addToast]);

  // Show toast when health check fails
  useEffect(() => {
    if (isHealthError) {
      addToast({
        type: 'warning',
        title: 'Connection Issue',
        message: 'Unable to connect to the backend server.',
        duration: 10000,
      });
    }
  }, [isHealthError, addToast]);

  // Render ThesesPage if in theses view
  if (currentView === 'theses') {
    return (
      <div className="flex min-h-screen bg-background font-sans text-foreground antialiased selection:bg-primary/20 selection:text-primary">
        <Sidebar onNavigate={setCurrentView} currentView={currentView} />
        <main className={cn(
          "flex flex-1 flex-col transition-all duration-300 ease-in-out",
          "md:ml-64",
          isCollapsed && "md:ml-16"
        )}>
          <Header />
          <ThesesPage onBack={() => setCurrentView('dashboard')} />
        </main>
      </div>
    );
  }

  // Render AlertsCenter if in alerts view
  if (currentView === 'alerts') {
    return (
      <div className="flex min-h-screen bg-background font-sans text-foreground antialiased selection:bg-primary/20 selection:text-primary">
        <Sidebar onNavigate={setCurrentView} currentView={currentView} />
        <main className={cn(
          "flex flex-1 flex-col transition-all duration-300 ease-in-out p-6",
          "md:ml-64",
          isCollapsed && "md:ml-16"
        )}>
          <Header />
          <div className="flex-1 mt-6">
             <AlertsCenter />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-background font-sans text-foreground antialiased selection:bg-primary/20 selection:text-primary">
      {/* Fixed Sidebar */}
      <Sidebar onNavigate={setCurrentView} currentView={currentView} />

      {/* Main Content Area */}
      <main className={cn(
        "flex flex-1 flex-col transition-all duration-300 ease-in-out",
        // Desktop: adjust margin based on sidebar state
        "md:ml-64",
        isCollapsed && "md:ml-16"
      )}>
        {/* Top Bar */}
        <Header />

        {/* Dashboard Content Padded Area */}
        <div className="p-4 md:p-6 lg:p-8">
          
          {/* Control Bar (Input & Quick Select) */}
          <div className="mb-6 grid grid-cols-1 gap-4 lg:grid-cols-12 lg:gap-6">
            <div className="lg:col-span-8">
              <TickerInput ref={tickerInputRef} onAnalyze={handleAnalyze} disabled={isLoading} />
            </div>
            <div className="lg:col-span-4">
               <QuickSelect onSelect={handleAnalyze} disabled={isLoading} />
            </div>
          </div>

          {/* Main Display Area */}
          <AnimatePresence mode="wait">
            {error && (
              <motion.div
                key="error"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mb-6 rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-destructive"
              >
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5" />
                  <span className="font-semibold">Analysis Failed</span>
                </div>
                <p className="mt-1 text-sm opacity-90">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>
          
          <AnimatePresence mode="wait">
            {isLoading && selectedTicker ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
                animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
                transition={{ duration: 0.3 }}
              >
                <StreamingAnalysisProgress 
                  ticker={selectedTicker}
                  isStreaming={streaming.isStreaming}
                  progress={streaming.progress}
                  currentTool={streaming.currentTool}
                  events={streaming.events}
                  partialData={streaming.partialData}
                  error={streaming.error}
                  onCancel={handleCancel}
                />
              </motion.div>
            ) : !isLoading && analysisData ? (
              <motion.div
                key="results"
                initial={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
                animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
                transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
                className="space-y-4"
              >
                {/* Kill Alerts Banner */}
                {killAlerts.length > 0 && (
                  <KillAlertBanner
                    alerts={killAlerts}
                    onDismiss={(id) => setKillAlerts(prev => prev.filter(a => a.id !== id))}
                    onAcknowledge={(id) => {
                      setKillAlerts(prev => prev.filter(a => a.id !== id));
                      addToast({ type: 'info', title: 'Alert Acknowledged', message: 'Review your thesis to take action.' });
                    }}
                    onViewThesis={() => setCurrentView('theses')}
                  />
                )}
                
                <ResultsTabs 
                  result={analysisData} 
                  onRefresh={handleRefresh}
                  isRefreshing={isLoading}
                />
              </motion.div>
            ) : !isLoading && !error ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
                animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                exit={{ opacity: 0, scale: 0.98, filter: "blur(10px)" }}
                transition={{ duration: 0.4 }}
              >
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:gap-6">
                  <div className="lg:col-span-8">
                     <EmptyState type="welcome" />
                  </div>
                  <div className="lg:col-span-4">
                     <AnalysisHistory onSelectHistory={handleSelectHistory} />
                  </div>
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </main>

      {/* Status Indicator (Fixed Bottom Right) */}
      <div className="fixed bottom-4 right-4 z-50 md:bottom-6 md:right-6">
        <div className={cn(
          "flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold shadow-lg backdrop-blur-md border",
          backendStatus === 'online' 
            ? 'bg-success/10 text-success border-success/20' 
            : 'bg-destructive/10 text-destructive border-destructive/20'
        )}>
           <div className={cn(
             "h-2.5 w-2.5 shrink-0 rounded-full ring-2 ring-background",
             backendStatus === 'online'
               ? 'bg-success shadow-[0_0_10px_rgba(34,197,94,0.55)]'
               : 'bg-destructive shadow-[0_0_10px_rgba(239,68,68,0.45)]'
           )} />
           {backendStatus === 'online' ? 'Agent Available' : 'Agent Unavailable'}
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <AuthProvider>
          <SidebarProvider>
            <ToastProvider>
              <AppContent />
            </ToastProvider>
          </SidebarProvider>
        </AuthProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
