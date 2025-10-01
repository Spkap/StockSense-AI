import React from 'react';
import Button from '../ui/Button';

const EmptyWatchlist = ({ onAddStock, actionLoading }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 bg-black">
      <div className="text-6xl mb-4"></div>
      <div className="text-center">
        <h3 className="text-lg font-semibold mb-2 text-white">No stocks added yet</h3>
        <p className="text-base-content/70 mb-4 text-white">Start building your watchlist by adding some stocks to track</p>


        <Button
        className="btn btn-warning"
        onClick={onAddStock}
        disabled={actionLoading}
        aria-label="Add first stock to watchlist"
        >
        <span className="font-bold">Add Stocks</span>
        </Button>

       
      </div>
    </div>
  );
};

export default EmptyWatchlist;