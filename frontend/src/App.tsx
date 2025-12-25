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
import { useAppKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useHealthCheck, useAnalysisResults } from './api/hooks';
import { useStreamingAnalysis } from './hooks/useStreamingAnalysis';
import type { AnalysisData, KillAlert } from './types/api';
import { AlertCircle } from 'lucide-react';
import { cn } from './utils/cn';

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
  
  // Fetch cached results when ticker changes
  const { data: resultsData, refetch: refetchResults } = useAnalysisResults(selectedTicker);
  
  // Use streaming final data or cached results
  const analysisData: AnalysisData | null = 
    streaming.finalData || resultsData?.data || null;

  const handleAnalyze = (ticker: string, _force: boolean = false) => {
    setSelectedTicker(ticker);
    setKillAlerts([]);
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
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
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
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ duration: 0.4, type: "spring", stiffness: 100 }}
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
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
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
             "h-2 w-2 rounded-full",
             backendStatus === 'online' ? 'bg-success' : 'bg-destructive'
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
        <SidebarProvider>
          <ToastProvider>
            <AppContent />
          </ToastProvider>
        </SidebarProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
