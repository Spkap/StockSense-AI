import React, { useState, useEffect } from 'react';
import Button from '../ui/Button';
import { X, TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';
import { stockAPI } from '../../services/api/stockAPI';

const StockCard = ({ 
  stockItem, 
  onAnalyze, 
  onRemove, 
  actionLoading 
}) => {
  const [priceData, setPriceData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchPriceData();
    
    const interval = setInterval(() => {
      fetchPriceData();
    }, 300000); // 5 minutes = 300,000 milliseconds
    
    return () => clearInterval(interval);
  }, [stockItem.stock.symbol]);

  const fetchPriceData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await stockAPI.getPriceData(stockItem.stock.symbol);
      
      // Check for API errors
      if (data['Error Message']) {
        throw new Error(data['Error Message']);
      }
      
      if (data['Note']) {
        throw new Error('API call frequency limit reached. Please try again later.');
      }
      
      if (data && data['Time Series (1min)']) {
        const timeSeries = data['Time Series (1min)'];
        const timestamps = Object.keys(timeSeries).sort((a, b) => new Date(b) - new Date(a));
        
        if (timestamps.length >= 2) {
          const currentPrice = parseFloat(timeSeries[timestamps[0]]['4. close']);
          const previousPrice = parseFloat(timeSeries[timestamps[1]]['4. close']);
          const change = currentPrice - previousPrice;
          const changePercent = ((change / previousPrice) * 100);
          
          setPriceData({
            currentPrice,
            previousPrice,
            change,
            changePercent,
            isUp: change >= 0,
            timestamp: timestamps[0],
            volume: parseInt(timeSeries[timestamps[0]]['5. volume'])
          });
        } else {
          throw new Error('Insufficient price data available');
        }
      } else {
        throw new Error('No price data available for this symbol');
      }
    } catch (err) {
      console.error('Error fetching price data for', stockItem.stock.symbol, err);
      setError(err.message || 'Failed to load price data');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = () => {
    if (confirm(`Remove ${stockItem.stock.symbol} from the watchlist?`)) {
      onRemove(stockItem.stock.id);
    }
  };

  return (
    <div className="card bg-black border border-base-300">
      <div className="card-body py-4 px-4">
        <div className="flex justify-between items-center">
          <div className="flex-1">
            <div className="flex items-center justify-between">
              {/* Stock Info */}
              <div>
                <div className="font-bold text-3xl text-white">{stockItem.stock.symbol}</div>
                <div className="text-sm text-white/70">{stockItem.stock.name}</div>
              </div>
              
              {/* Price Data */}
              <div className="text-right">
                {loading ? (
                  <div className="flex items-center gap-2">
                    <span className="loading loading-spinner loading-sm"></span>
                    <span className="text-white/50 text-sm">Loading...</span>
                  </div>
                ) : error ? (
                  <div className="text-red-400 text-sm">
                    <span>Price unavailable</span>
                  </div>
                ) : priceData ? (
                  <div className="flex flex-col items-end">
                    {/* Current Price */}
                    <div className="text-2xl font-bold text-white">
                      ${priceData.currentPrice.toFixed(2)}
                    </div>
                    
                    {/* Price Change */}
                    <div className={`flex items-center gap-1 text-sm font-medium ${
                      priceData.isUp ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {priceData.isUp ? (
                        <TrendingUp className="w-4 h-4" />
                      ) : (
                        <TrendingDown className="w-4 h-4" />
                      )}
                      <span>
                        {priceData.isUp ? '+' : ''}${priceData.change.toFixed(2)} 
                        ({priceData.isUp ? '+' : ''}{priceData.changePercent.toFixed(2)}%)
                      </span>
                    </div>
                    
                  </div>
                ) : (
                  <div className="text-white/50 text-sm">No data</div>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="flex items-center justify-between w-full gap-2 mt-4">
          <Button
            className="btn btn-warning flex-1"
            onClick={() => onAnalyze(stockItem.stock)}
            disabled={actionLoading}
            title={`Analyze ${stockItem.stock.symbol} with AI`}
            aria-label={`Analyze ${stockItem.stock.symbol}`}
          >
            <span className="font-bold text-lg">Analyze</span>
          </Button>
          
          <button
            className="btn btn-circle btn-error btn-sm"
            onClick={handleRemove}
            disabled={actionLoading}
            title={`Remove ${stockItem.stock.symbol} from watchlist`}
            aria-label={`Remove ${stockItem.stock.symbol}`}
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default StockCard;