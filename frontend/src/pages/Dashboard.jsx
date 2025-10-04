import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/ToastProvider';
import { watchlistAPI } from '../services/api/watchlistAPI';
import { analysisAPI } from '../services/api/analysisAPI';
import Header from '../components/layout/Header';
import WatchlistCard from '../components/watchlist/WatchlistCard';
import AnalysisDashboard from '../components/analysis/AnalysisDashboard';
import NewsCard from '../components/news/NewsCard';
import StockChartDashboard from '../components/analysis/StockChartDashboard';

const Dashboard = () => {
  const { currentUser } = useAuth();
  const { showSuccess, showError } = useToast();
  const [watchlist, setWatchlist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAnalysis, setShowAnalysis] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [analyzingStock, setAnalyzingStock] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
      setLoading(true);
      const data = await watchlistAPI.getWatchlist();
      console.log('Fetched watchlist data:', data);
      setWatchlist(data);
    } catch (err) {
      showError(`Failed to load watchlist: ${err.message}`);
      console.error('Failed to fetch watchlist:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeStock = async (stock) => {
    try {
      console.log('Starting analysis for stock:', stock);
      
      // Clear any previous analysis data first
      setAnalysisData(null);
      
      // Set loading states immediately
      setAnalyzingStock(stock);
      setAnalysisLoading(true);
      setShowAnalysis(true);
      
      console.log('Analysis states set - loading:', true, 'showAnalysis:', true, 'stock:', stock);
      
      showSuccess(`Starting AI analysis for ${stock.symbol}...`);
      
      const analysis = await analysisAPI.analyzeStock(stock.symbol);
      console.log('Analysis response received:', analysis);
      setAnalysisData(analysis);
      
      showSuccess(`Analysis completed for ${stock.symbol}!`);
      
    } catch (err) {
      console.error('Analysis error:', err);
      showError(`Failed to analyze ${stock.symbol}: ${err.message}`);
    } finally {
      console.log('Setting analysis loading to false');
      setAnalysisLoading(false);
    }
  };

  const closeAnalysis = () => {
    console.log('Closing analysis modal');
    setShowAnalysis(false);
    setAnalysisData(null);
    setAnalyzingStock(null);
    setAnalysisLoading(false);
    
    console.log('Analysis modal closed, should show dashboard');
  };

  // Ensure body has proper styling (in case modal messed it up)
  useEffect(() => {
    document.body.style.overflow = (showAnalysis || analysisLoading) ? 'hidden' : 'auto';
    document.body.style.backgroundColor = '#121212';
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [showAnalysis, analysisLoading]);

  return (
    <div className="min-h-screen bg-black">
      <Header />

      {/* Main Content - Always visible */}
      <main className="px-6 py-8">
        <div className="space-y-6">
          

          <div className="grid grid-cols-1 xl:grid-cols-10 gap-6">
            <div className="xl:col-span-7 pl-2">
              <StockChartDashboard />
            </div>

            <div className="xl:col-span-3 space-y-6 pr-2">
              <div className="relative">
                {!watchlist ? (
                  loading ? (
                    <div className="card bg-black shadow-xl">
                      <span className="loading loading-spinner loading-lg"></span>
                      <h4>Loading your watchlist...</h4>
                    </div>
                  ) : (
                    <div className="card bg-black shadow-xl">
                      <h4>Watchlist Not Found</h4>
                      <button onClick={fetchWatchlist}>Try Again</button>
                    </div>
                  )
                ) : (
                  <>
                    <WatchlistCard
                      watchlist={watchlist}
                      onAnalyzeStock={handleAnalyzeStock}
                      onWatchlistUpdate={fetchWatchlist}
                      showDeleteButton={false}
                      isLoading={loading} 
                    />
                    
                  </>
                )}
              </div>

              {/* News Section */}
              {!loading && watchlist && (
                <NewsCard />
              )}
              {/* Show placeholder if no watchlist */}
              {!loading && !watchlist && (
                <div className="bg-black border border-white rounded-lg p-6 h-fit">
                  <h2 className="text-white text-xl font-bold mb-4">News</h2>
                  <div className="text-center py-8">
                    <p className="text-white/70">Add stocks to your watchlist to see related news</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      {/* Analysis Dashboard Modal */}
      {analyzingStock && (showAnalysis || analysisLoading) && (
        <AnalysisDashboard
          key={`analysis-${analyzingStock.symbol}-${Date.now()}`} 
          analysisData={analysisData}
          stock={analyzingStock}
          onClose={closeAnalysis}
          loading={analysisLoading}
        />
      )}
    </div>
  );
};

export default Dashboard;
