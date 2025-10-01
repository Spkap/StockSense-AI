import React from 'react';
import WatchlistHeader from './WatchlistHeader';
import EmptyWatchlist from './EmptyWatchlist';
import StockCard from './StockCard';

const WatchlistCard = ({ 
  watchlist, 
  onDelete, 
  onAddStock, 
  onRemoveStock, 
  onAnalyzeStock,
  actionLoading,
  showDeleteButton = true 
}) => {
  const stockCount = watchlist.stocks ? watchlist.stocks.length : 0;

  return (
    <div className="card bg-black shadow-xl border border-base-300">
      <div className="card-body">
        <WatchlistHeader
          watchlist={watchlist}
          stockCount={stockCount}
          onAddStock={onAddStock}
          onDelete={onDelete}
          actionLoading={actionLoading}
          showDeleteButton={showDeleteButton}
        />
        
        
        {!watchlist.stocks || watchlist.stocks.length === 0 ? (
          <EmptyWatchlist
            onAddStock={onAddStock}
            actionLoading={actionLoading}
          />
        ) : (
          <div className="space-y-3">
            {watchlist.stocks.map(stockItem => (
              <StockCard
                key={stockItem.id}
                stockItem={stockItem}
                onAnalyze={onAnalyzeStock}
                onRemove={onRemoveStock}
                actionLoading={actionLoading}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default WatchlistCard;
