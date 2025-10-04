import React, { useState } from 'react';
import { useToast } from '../ui/ToastProvider';
import { watchlistAPI } from '../../services/api/watchlistAPI';
import { stockAPI } from '../../services/api/stockAPI';
import WatchlistHeader from './WatchlistHeader';
import EmptyWatchlist from './EmptyWatchlist';
import StockCard from './StockCard';
import AddStockModal from './AddStockModal';

const WatchlistCard = ({ 
  watchlist, 
  onDelete, 
  onAnalyzeStock,
  onWatchlistUpdate,
  showDeleteButton = true,
  isLoading = false 
}) => {
  const { showSuccess, showError } = useToast();
  const [actionLoading, setActionLoading] = useState(false);
  const [showAddStockModal, setShowAddStockModal] = useState(false);
  const [stockSearch, setStockSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  const stockCount = watchlist.stocks ? watchlist.stocks.length : 0;

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
      await watchlistAPI.addStock({
        stock_id: stock.id
      });
      
      setStockSearch('');
      setSearchResults([]);
      setShowAddStockModal(false);
      showSuccess(`${stock.symbol} added to watchlist!`);
      
      if (onWatchlistUpdate) {
        await onWatchlistUpdate();
      }
      
    } catch (err) {
      showError(`Failed to add stock: ${err.message}`);
      console.error('Failed to add stock:', err);
    } finally {
      setTimeout(() => {
        setActionLoading(false);
      }, 500);
    }
  };

  const handleRemoveStock = async (stockId) => {
    try {
      setActionLoading(true);
      await watchlistAPI.removeStock(stockId);
      
      showSuccess('Stock removed from watchlist!');
      
      if (onWatchlistUpdate) {
        await onWatchlistUpdate();
      }
      
    } catch (err) {
      showError(`Failed to remove stock: ${err.message}`);
      console.error('Failed to remove stock:', err);
    } finally {
      setTimeout(() => {
        setActionLoading(false);
      }, 500);
    }
  };

  const openAddStockModal = () => {
    setShowAddStockModal(true);
    setStockSearch('');
    setSearchResults([]);
  };

  return (
    <>
      <div className="card bg-black-200 border border-white">
        <div className="card-body">
          <WatchlistHeader
            watchlist={watchlist}
            stockCount={stockCount}
            onAddStock={openAddStockModal}
            onDelete={onDelete}
            actionLoading={actionLoading}
            showDeleteButton={showDeleteButton}
          />
          
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <span className="loading loading-spinner loading-lg"></span>
              <div className="text-center mt-4">
                <h4 className="text-lg font-bold text-white">Updating watchlist...</h4>
                <p className="text-white">Fetching latest data</p>
              </div>
            </div>
          ) : !watchlist.stocks || watchlist.stocks.length === 0 ? (
            <EmptyWatchlist
              onAddStock={openAddStockModal}
              actionLoading={actionLoading}
            />
          ) : (
            <div className="space-y-3">
              {watchlist.stocks.map(stockItem => (
                <StockCard
                  key={stockItem.id}
                  stockItem={stockItem}
                  onAnalyze={onAnalyzeStock}
                  onRemove={handleRemoveStock}
                  actionLoading={actionLoading}
                />
              ))}
            </div>
          )}
        </div>
      </div>

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
    </>
  );
};

export default WatchlistCard;
