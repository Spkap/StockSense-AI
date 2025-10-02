import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ui/ToastProvider';
import { watchlistAPI } from '../services/api/watchlistAPI';
import { stockAPI } from '../services/api/stockAPI';
import { analysisAPI } from '../services/api/analysisAPI';
import Header from '../components/layout/Header';
import WatchlistCard from '../components/watchlist/WatchlistCard';
import AddStockModal from '../components/watchlist/AddStockModal';
import AnalysisDashboard from '../components/analysis/AnalysisDashboard';
import NewsCard from '../components/news/NewsCard';
import SimpleAnalysisTest from '../components/analysis/SimpleAnalysisTest';
import StockChartDashboard from '../components/analysis/StockChartDashboard';

const Dashboard = () => {
  const { currentUser } = useAuth();
  const { showSuccess, showError } = useToast();
  const [watchlist, setWatchlist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showAddStockModal, setShowAddStockModal] = useState(false);
  const [stockSearch, setStockSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [actionLoading, setActionLoading] = useState(false);
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

  const handleSearchStocks = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    try {
      const results = await stockAPI.getStocks(query);
      setSearchResults(results);
    } catch (err) {
      console.error('Failed to search stocks:', err);
      setSearchResults([]);
    }
  };

  const handleAddStock = async (stock) => {
    try {
      setActionLoading(true);
      const addedStock = await watchlistAPI.addStock({
        stock_id: stock.id
      });
      
      setStockSearch('');
      setSearchResults([]);
      setShowAddStockModal(false);
      showSuccess(`${stock.symbol} added to watchlist!`);
      
      // Refresh the watchlist data
      await fetchWatchlist();
      
    } catch (err) {
      showError(`Failed to add stock: ${err.message}`);
      console.error('Failed to add stock:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRemoveStock = async (stockId) => {
    try {
      setActionLoading(true);
      await watchlistAPI.removeStock(stockId);
      
      showSuccess('Stock removed from watchlist!');
      
      // Refresh the watchlist data
      await fetchWatchlist();
      
    } catch (err) {
      showError(`Failed to remove stock: ${err.message}`);
      console.error('Failed to remove stock:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const openAddStockModal = () => {
    setShowAddStockModal(true);
    setStockSearch('');
    setSearchResults([]);
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
      // Don't close the modal immediately, keep it open to show the error
      // setShowAnalysis(false);
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
              {loading ? (
                <div className="card bg-base-100 shadow-xl">
                  <div className="card-body">
                    <div className="flex flex-col items-center justify-center py-16">
                      <span className="loading loading-spinner loading-lg"></span>
                      <div className="text-center mt-4">
                        <h4 className="text-lg font-semibold">Loading your watchlist...</h4>
                        <p className="text-base-content/70">Fetching the latest market data</p>
                      </div>
                    </div>
                  </div>
                </div>
              ) : !watchlist ? (
                <div className="card bg-black shadow-xl">
                  <div className="card-body">
                    <div className="flex flex-col items-center justify-center py-16">
                      <h4 className="text-lg font-semibold mb-2">Watchlist Not Found</h4>
                      <p className="text-base-content/70 mb-6">Unable to load your watchlist. Please try again.</p>
                      <button onClick={fetchWatchlist} className="btn btn-outline btn-sm gap-2">
                        <span>↻</span>
                        Try Again
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <WatchlistCard
                  watchlist={watchlist}
                  onAddStock={openAddStockModal}
                  onRemoveStock={handleRemoveStock}
                  onAnalyzeStock={handleAnalyzeStock}
                  actionLoading={actionLoading}
                  showDeleteButton={false}
                />
              )}

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

      {/* Add Stock Modal */}
      <AddStockModal
        isOpen={showAddStockModal}
        onClose={() => setShowAddStockModal(false)}
        stockSearch={stockSearch}
        setStockSearch={setStockSearch}
        searchResults={searchResults}
        onSearchStocks={handleSearchStocks}
        onAddStock={handleAddStock}
        actionLoading={actionLoading}
      />

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
