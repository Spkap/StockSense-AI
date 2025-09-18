import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../components/ToastProvider';
import { watchlistAPI, stockAPI, analysisAPI } from '../services/api';
import Header from '../components/Header';
import WatchlistCard from '../components/WatchlistCard';
import AnalysisDashboard from '../components/AnalysisDashboard';
import SimpleAnalysisTest from '../components/SimpleAnalysisTest';

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
      console.log('Fetched watchlist data:', data); // Debug log
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
      setAnalyzingStock(stock);
      setAnalysisLoading(true);
      setShowAnalysis(true);
      
      showSuccess(`Starting AI analysis for ${stock.symbol}...`);
      
      const analysis = await analysisAPI.analyzeStock(stock.symbol);
      console.log('Analysis response received:', analysis);
      setAnalysisData(analysis);
      
      showSuccess(`Analysis completed for ${stock.symbol}!`);
      
    } catch (err) {
      console.error('Analysis error:', err);
      showError(`Failed to analyze ${stock.symbol}: ${err.message}`);
      setShowAnalysis(false);
      console.error('Failed to analyze stock:', err);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const closeAnalysis = () => {
    console.log('Closing analysis modal');
    setShowAnalysis(false);
    setAnalysisData(null);
    setAnalyzingStock(null);
    setAnalysisLoading(false);
    
    // Ensure we stay on dashboard by not navigating anywhere
    // The modal will just close and reveal the dashboard underneath
    console.log('Analysis modal closed, should show dashboard');
  };

  // Ensure body has proper styling (in case modal messed it up)
  useEffect(() => {
    document.body.style.overflow = showAnalysis ? 'hidden' : 'auto';
    document.body.style.backgroundColor = '#121212';
    
    return () => {
      document.body.style.overflow = 'auto';
    };
  }, [showAnalysis]);

  return (
    <div className="dashboard-container">
      <Header />

      {/* Main Content - Always visible */}
      <main className="dashboard-main">
        <div className="dashboard-content">
          {/* Welcome Section */}
          <section className="welcome-section">
            <div className="welcome-content">
              <h2>Welcome back, {currentUser?.displayName?.split(' ')[0] || 'User'}!</h2>
              <p>Get AI-powered market insights.</p>
            </div>
          </section>

          {/* Watchlist Section */}
          <section className="watchlist-section">
            <div className="watchlist-content">
              {loading ? (
                <div className="loading-state">
                  <div className="spinner-container">
                    <div className="spinner-large"></div>
                  </div>
                  <div className="loading-text">
                    <h4>Loading your watchlist...</h4>
                    <p>Fetching the latest market data</p>
                  </div>
                </div>
              ) : !watchlist ? (
                <div className="empty-state">
                  <div className="empty-icon"></div>
                  <h4>Watchlist Not Found</h4>
                  <p>Unable to load your watchlist. Please try again.</p>
                  <button onClick={fetchWatchlist} className="retry-button secondary-button">
                    <span className="button-icon">↻</span>
                    <span>Try Again</span>
                  </button>
                </div>
              ) : (
                <div className="watchlist-container">
                  <WatchlistCard
                    watchlist={watchlist}
                    onAddStock={openAddStockModal}
                    onRemoveStock={handleRemoveStock}
                    onAnalyzeStock={handleAnalyzeStock}
                    actionLoading={actionLoading}
                    showDeleteButton={false}
                  />
                </div>
              )}
            </div>
          </section>        
        </div>
      </main>

      {/* Add Stock Modal */}
      {showAddStockModal && (
        <div className="modal-overlay" onClick={() => setShowAddStockModal(false)}>
          <div className="modal-content add-stock-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <h3>Add Stock to Watchlist</h3>
                <p>Search and add stocks to track their performance</p>
              </div>
              <button 
                className="close-button"
                onClick={() => setShowAddStockModal(false)}
                aria-label="Close modal"
              >
                ×
              </button>
            </div>
            
            <div className="modal-body">
              <div className="form-group">
                <label htmlFor="stock-search">Search Stocks</label>
                <div className="search-input-container">
                  <input
                    id="stock-search"
                    type="text"
                    value={stockSearch}
                    onChange={(e) => {
                      setStockSearch(e.target.value);
                      handleSearchStocks(e.target.value);
                    }}
                    placeholder="Search by symbol or name (e.g., AAPL, Apple)..."
                    autoFocus
                    className="search-input"
                  />
                  <div className="search-icon"></div>
                </div>
              </div>
              
              {searchResults.length > 0 && (
                <div className="search-results">
                  <h4 className="results-title">Search Results</h4>
                  <div className="results-list">
                    {searchResults.slice(0, 10).map(stock => (
                      <div key={stock.id} className="search-result-item">
                        <div className="stock-info">
                          <div className="stock-details">
                            <span className="stock-symbol">{stock.symbol}</span>
                            <span className="stock-name">{stock.name}</span>
                          </div>
                        </div>
                        <button
                          className="add-button primary-button small"
                          onClick={() => handleAddStock(stock)}
                          disabled={actionLoading}
                        >
                          {actionLoading ? (
                            <span className="spinner-small"></span>
                          ) : (
                            <>
                              <span className="button-icon">+</span>
                              <span>Add</span>
                            </>
                          )}
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="modal-footer">
              <button 
                type="button" 
                className="cancel-button secondary-button"
                onClick={() => setShowAddStockModal(false)}
                disabled={actionLoading}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Dashboard Modal */}
      {showAnalysis && analyzingStock && (
        <AnalysisDashboard
          key={`analysis-${analyzingStock.symbol}-${Date.now()}`} // Force remount
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
