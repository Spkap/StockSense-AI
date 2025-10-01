import React from 'react';
import Button from '../ui/Button';
import { X } from 'lucide-react';


const StockCard = ({ 
  stockItem, 
  onAnalyze, 
  onRemove, 
  actionLoading 
}) => {
  const handleRemove = () => {
    if (confirm(`Remove ${stockItem.stock.symbol} from the watchlist?`)) {
      onRemove(stockItem.stock.id);
    }
  };

  return (
    <div className="card bg-black border border-base-300">
      <div className="card-body py-4 px-2">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              
              <div>
                <div className="font-bold text-4xl text-white">{stockItem.stock.symbol}</div>
                <div className="text-sm text-base-content/70 text-white">{stockItem.stock.name}</div>
              </div>
            </div>
          </div>
          <div className="flex gap-2">

        <div class="flex items-center justify-between w-full gap-2">
             <Button
                className="btn btn-warning"
                onClick={() => onAnalyze(stockItem.stock)}
                disabled={actionLoading}
                title={`Analyze ${stockItem.stock.symbol} with AI`}
                aria-label={`Analyze ${stockItem.stock.symbol}`}
            ><span className="font-bold text-lg">Analyze</span>
            </Button>
            <button
              className="btn btn-circle btn-error btn-sm"
              onClick={handleRemove}
              disabled={actionLoading}
              title={`Remove ${stockItem.stock.symbol} from watchlist`}
              aria-label={`Remove ${stockItem.stock.symbol}`}
            >
            <X />
            </button>

        </div>





          </div>
        </div>
      </div>
    </div>
  );
};

export default StockCard;