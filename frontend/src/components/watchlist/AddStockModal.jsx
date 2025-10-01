import React from 'react';

const AddStockModal = ({ 
  isOpen, 
  onClose, 
  stockSearch, 
  setStockSearch, 
  searchResults, 
  onSearchStocks, 
  onAddStock, 
  actionLoading 
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box bg-black">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="font-bold text-lg text-white">Add Stock to Watchlist</h3>
            <p className="text-sm text-white/50">Search and add stocks to track their performance</p>
          </div>
          <button 
            className="btn btn-sm btn-circle btn-error"
            onClick={onClose}
            aria-label="Close modal"
          >
            ✕
          </button>
        </div>
        
        <div className="space-y-5">
          <div className="form-control">
            <label className="label" htmlFor="stock-search">
              <span className="label-text">Search Stocks</span>
            </label>
            <input
              id="stock-search"
              type="text"
              value={stockSearch}
              onChange={(e) => {
                setStockSearch(e.target.value);
                onSearchStocks(e.target.value);
              }}
              placeholder="Search by symbol or name"
              autoFocus
              className="input input-warning bg-gray-800 text-white w-full"
            />
          </div>
          
          {searchResults.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-semibold text-white">Search Results</h4>
              <div className="max-h-60 overflow-y-auto space-y-2">
                {searchResults.slice(0, 10).map(stock => (
                  <div key={stock.id} className="card bg-black border-base-300">
                    <div className="card-body py-3 px-4">
                      <div className="flex justify-between items-center">
                        <div>
                          <div className="font-bold text-white">{stock.symbol}</div>
                          <div className="text-sm text-white/70">{stock.name}</div>
                        </div>
                        <button
                          className="btn btn-warning btn-sm gap-2"
                          onClick={() => onAddStock(stock)}
                          disabled={actionLoading}
                        >
                          {actionLoading ? (
                            <span className="loading loading-spinner loading-xs"></span>
                          ) : (
                            <>
                              Add
                            </>
                          )}
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        
        <div className="modal-action">
          <button 
            type="button" 
            className="btn btn-warning"
            onClick={onClose}
            disabled={actionLoading}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddStockModal;