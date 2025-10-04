import React from 'react';
import Button from '../ui/Button';
import { Plus } from 'lucide-react';


const WatchlistHeader = ({ 
  watchlist, 
  onAddStock, 
  onDelete, 
  actionLoading, 
  showDeleteButton 
}) => {
  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this watchlist?')) {
      onDelete(watchlist.id);
    }
  };

  return (
    <div className="card-title flex justify-between items-start mb-4">
      <div className="flex-1">
        <h2 className="card-title text-xl text-white font-bold">{watchlist.name}</h2>
      </div>
      <div className="flex gap-2">

        <Button
        className="btn btn-warning btn-circle"
        onClick={onAddStock}
        disabled={actionLoading}
        aria-label="Add stock to watchlist"
        
        >
        <Plus />

        </Button>
        
        {showDeleteButton && (
          <button 
            className="btn btn-error btn-sm"
            onClick={handleDelete}
            disabled={actionLoading}
            title="Delete watchlist"
            aria-label={`Delete ${watchlist.name} watchlist`}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
};

export default WatchlistHeader;