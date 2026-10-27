import { useState, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from './api/hooks';
import { motion, AnimatePresence } from 'framer-motion';
import Header from './components/Header';
import CommandRail from './components/CommandRail';
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
import { ToastProvider, useToast } from './components/ui/toast';
import { useAppKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import { useHealthCheck, useAnalysisResults } from './api/hooks';
import { useStreamingAnalysis } from './hooks/useStreamingAnalysis';
import type { AnalysisData, KillAlert } from './types/api';
import { AlertCircle } from 'lucide-react';
import { useAuth } from './context/AuthContext';

function AppContent() {
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'dashboard' | 'theses' | 'alerts'>('dashboard');
  const { addToast } = useToast();
  const queryClient = useQueryClient();
  const { user, loading: authLoading } = useAuth();
  const tickerInputRef = useRef<TickerInputRef>(null);
  
  // Keyboard shortcuts (Cmd/Ctrl+K to focus search)
  useAppKeyboardShortcuts({
    onFocusSearch: () => tickerInputRef.current?.focus(),
  });
  
  // Health check
  const { isError: isHealthError } = useHealthCheck();
  
  // Streaming Analysis (Stage 4)
  const streaming = useStreamingAnalysis();
  const [killAlerts, setKillAlerts] = useState<KillAlert[]>([]);
  const owner = user?.id || 'guest';
  const previousOwner = useRef(owner);
  useEffect(() => {
    if (!authLoading && previousOwner.current !== owner) {
      streaming.reset();
      setSelectedTicker(null);
      previousOwner.current = owner;
    }
  }, [owner, authLoading, streaming.reset]);
  
  // Fetch cached results when ticker changes
  const { data: resultsData, refetch: refetchResults, isLoading: isResultsLoading, error: resultsError } = useAnalysisResults(streaming.isStreaming ? null : selectedTicker);
  
  // Use streaming final data or cached results
  const analysisData: AnalysisData | null =
    !authLoading && previousOwner.current === owner ? (streaming.finalData || resultsData?.data || null) : null;

  const handleAnalyze = (ticker: string, _force: boolean = false) => {
    if (authLoading) return;
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
      queryClient.invalidateQueries({ queryKey: queryKeys.cachedTickers });
    }
  }, [streaming.finalData, selectedTicker, refetchResults, queryClient]);

  const isLoading = streaming.isStreaming;
  const error = streaming.error || (!streaming.isStreaming && selectedTicker && !streaming.finalData && resultsError ? resultsError.message : null);

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
      <div className="flex min-h-screen bg-canvas font-mono text-txt-primary selection:bg-accent selection:text-canvas antialiased relative">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
        <CommandRail onNavigate={setCurrentView} currentView={currentView} />
        <main className="flex min-w-0 flex-1 flex-col ml-14 relative z-10">
          <Header />
          <ThesesPage onBack={() => setCurrentView('dashboard')} />
        </main>
      </div>
    );
  }

  // Render AlertsCenter if in alerts view
  if (currentView === 'alerts') {
    return (
      <div className="flex min-h-screen bg-canvas font-mono text-txt-primary selection:bg-accent selection:text-canvas antialiased relative">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
        <CommandRail onNavigate={setCurrentView} currentView={currentView} />
        <main className="flex min-w-0 flex-1 flex-col ml-14 p-6 relative z-10">
          <Header />
          <div className="flex-1 mt-6">
             <AlertsCenter />
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-canvas font-mono text-txt-primary selection:bg-accent selection:text-canvas antialiased relative">
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:32px_32px] pointer-events-none" />
      {/* 48px Command Rail (Sidebar Replacement) */}
      <CommandRail onNavigate={setCurrentView} currentView={currentView} />

      {/* Main Content Area */}
      <main className="flex min-w-0 flex-1 flex-col ml-14 relative z-10">
        {/* Top Bar */}
        <Header />

        {/* Dashboard Content Padded Area */}
        <div className="w-full max-w-[1440px] mx-auto p-4 md:p-6 lg:p-8">
          
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
                className="mb-6 rounded-sm border border-bear/50 bg-bear/10 p-4 text-bear"
              >
                <div className="flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" />
                  <span className="font-mono text-sm uppercase tracking-widest font-bold">Analysis unavailable</span>
                </div>
                <p className="mt-2 text-sm font-mono">{error}</p>
                <div className="mt-3 flex gap-4 text-sm">
                  {selectedTicker && <button className="underline" onClick={() => handleAnalyze(selectedTicker)}>Retry analysis</button>}
                  {resultsData?.data?.ticker?.toUpperCase() === selectedTicker?.toUpperCase() && <button className="underline" onClick={() => streaming.reset()}>View saved research</button>}
                  <button className="underline" onClick={() => { streaming.reset(); setSelectedTicker(null); }}>Back to dashboard</button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          <AnimatePresence mode="wait">
            {isResultsLoading && selectedTicker && !isLoading ? (
              <div role="status" className="py-16 text-center text-txt-secondary">Loading saved research for {selectedTicker}…</div>
            ) : isLoading && selectedTicker ? (
              <motion.div
                key="loading"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15, ease: "linear" }}
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
            ) : !isLoading && !error && analysisData ? (
              <motion.div
                key="results"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15, ease: "linear" }}
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
                <AnalysisHistory onSelectHistory={handleSelectHistory} onRemoved={ticker => { if (selectedTicker === ticker) { streaming.reset(); setSelectedTicker(null); } }} />
              </motion.div>
            ) : !isLoading && !error ? (
              <motion.div
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.15 }}
              >
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-12 lg:gap-6">
                  <div className="lg:col-span-8">
                     <EmptyState type="welcome" />
                  </div>
                  <div className="lg:col-span-4">
                     <AnalysisHistory onSelectHistory={handleSelectHistory} onRemoved={ticker => { if (selectedTicker === ticker) { streaming.reset(); setSelectedTicker(null); } }} />
                  </div>
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </main>


    </div>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <ToastProvider>
          <AppContent />
        </ToastProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

export default App;

