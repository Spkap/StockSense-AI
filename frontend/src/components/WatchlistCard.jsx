import React from 'react';

const WatchlistCard = ({ 
  watchlist, 
  onDelete, 
  onAddStock, 
  onRemoveStock, 
  onAnalyzeStock,
  actionLoading,
  showDeleteButton = true 
}) => {
  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this watchlist?')) {
      onDelete(watchlist.id);
    }
  };

  const handleRemoveStock = (stockId) => {
    if (confirm('Remove this stock from the watchlist?')) {
      onRemoveStock(stockId);
    }
  };

  const stockCount = watchlist.stocks ? watchlist.stocks.length : 0;

  return (
    <article className="watchlist-card">
      <header className="watchlist-header">
        <div className="watchlist-title">
          <h4 className="watchlist-name">{watchlist.name}</h4>
          <span className="stock-count">{stockCount} stock{stockCount !== 1 ? 's' : ''} tracked</span>
        </div>
        <div className="watchlist-actions">
          <button 
            className="primary-button small"
            onClick={() => onAddStock()}
            disabled={actionLoading}
            aria-label="Add stock to watchlist"
          >
            <span className="button-icon">+</span>
            Add Stock
          </button>
          {showDeleteButton && (
            <button 
              className="delete-button"
              onClick={handleDelete}
              disabled={actionLoading}
              title="Delete watchlist"
              aria-label={`Delete ${watchlist.name} watchlist`}
            >
              <span className="button-icon">Delete</span>
            </button>
          )}
        </div>
      </header>
      
      <main className="watchlist-content">
        <div className="watchlist-preview">
          {!watchlist.stocks || watchlist.stocks.length === 0 ? (
            <div className="empty-watchlist">
              <div className="empty-icon"></div>
              <div className="empty-content">
                <h5>No stocks added yet</h5>
                <p>Start building your watchlist by adding some stocks to track</p>
                <button 
                  className="primary-button"
                  onClick={() => onAddStock()}
                  disabled={actionLoading}
                  aria-label="Add first stock to watchlist"
                >
                  <span className="button-icon">+</span>
                  Add Stock
                </button>
              </div>
            </div>
          ) : (
            <div className="stock-list">
              {watchlist.stocks.map(stockItem => (
                <div key={stockItem.id} className="stock-item">
                  <div className="stock-info">
                    <span className="stock-symbol">{stockItem.stock.symbol}</span>
                    <span className="stock-name">{stockItem.stock.name}</span>
                  </div>
                  <div className="stock-actions">
                    <button
                      className="secondary-button small"
                      onClick={() => onAnalyzeStock(stockItem.stock)}
                      disabled={actionLoading}
                      title={`Analyze ${stockItem.stock.symbol} with AI`}
                      aria-label={`Analyze ${stockItem.stock.symbol}`}
                    >
                      Analyze
                    </button>
                    <button
                      className="remove-button"
                      onClick={() => handleRemoveStock(stockItem.stock.id)}
                      disabled={actionLoading}
                      title={`Remove ${stockItem.stock.symbol} from watchlist`}
                      aria-label={`Remove ${stockItem.stock.symbol}`}
                    >
                      <span className="button-icon">×</span>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </article>
  );
};

export default WatchlistCard;
