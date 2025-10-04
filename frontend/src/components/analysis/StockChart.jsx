import React, { useEffect, useRef, useState } from 'react';

const StockChart = ({ ticker }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const [isLoading, setIsLoading] = useState(false);
  const [scriptLoaded, setScriptLoaded] = useState(false);

  // Check if TradingView script is loaded
  useEffect(() => {
    console.log('Checking TradingView script availability...');
    
    const checkTradingView = () => {
      if (window.TradingView) {
        console.log('TradingView script found immediately');
        setScriptLoaded(true);
      } else {
        console.log('TradingView script not found, polling...');
        // Poll for TradingView availability
        const pollInterval = setInterval(() => {
          if (window.TradingView) {
            console.log('TradingView script loaded via polling');
            setScriptLoaded(true);
            clearInterval(pollInterval);
          }
        }, 100);

        // Cleanup after 10 seconds
        const timeout = setTimeout(() => {
          console.log('TradingView script polling timeout after 10 seconds');
          clearInterval(pollInterval);
        }, 10000);

        return () => {
          clearInterval(pollInterval);
          clearTimeout(timeout);
        };
      }
    };

    checkTradingView();
  }, []);

  useEffect(() => {
    console.log('Chart creation useEffect triggered:', { ticker, scriptLoaded, containerReady: !!chartContainerRef.current });
    
    if (!ticker || !chartContainerRef.current || !scriptLoaded) {
      console.log('Conditions not met for chart creation:', { ticker, scriptLoaded, containerReady: !!chartContainerRef.current });
      return;
    }

    console.log('Setting loading to true for ticker:', ticker);
    setIsLoading(true);

    if (chartRef.current) {
      try {
        chartRef.current.remove();
      } catch (error) {
        console.warn('Error removing previous chart:', error);
      }
      chartRef.current = null;
    }

    chartContainerRef.current.innerHTML = '';

    const containerId = `tradingview-chart-${ticker}-${Date.now()}`;
    chartContainerRef.current.id = containerId;

    console.log('Creating TradingView widget for:', ticker, 'in container:', containerId);

    // Create new chart with a slight delay to ensure container is ready
    const timeoutId = setTimeout(() => {
      try {
        chartRef.current = new window.TradingView.widget({
          // Essential settings
          width: '100%',
          height: 400,
          symbol: `NASDAQ:${ticker}`,
          interval: 'D',
          timezone: 'Etc/UTC',
          theme: 'dark',
          style: '1', // Candlestick chart
          locale: 'en',
          container_id: containerId,
          
          // Clean UI settings
          hide_top_toolbar: true,
          hide_legend: false,
          hide_side_toolbar: true,
          toolbar_bg: '#1f2937',
          enable_publishing: false,
          allow_symbol_change: false,
          save_image: false,
          show_popup_button: false,
          
          // Simplified appearance
          hide_volume: false,
          backgroundColor: '#1f2937',
          gridColor: '#374151',
          
          // Chart ready callback
          onChartReady: () => {
            console.log('Chart ready callback triggered for:', ticker);
            setIsLoading(false);
          }
        });
        console.log('TradingView widget created successfully');
        
        // Fallback timeout in case onChartReady doesn't fire
        setTimeout(() => {
          console.log('Fallback timeout triggered, setting loading to false');
          setIsLoading(false);
        }, 5000);
        
      } catch (error) {
        console.error('Error creating TradingView chart:', error);
        setIsLoading(false);
      }
    }, 100);

    // Cleanup function
    return () => {
      console.log('Cleanup function called for ticker:', ticker);
      clearTimeout(timeoutId);
      if (chartRef.current) {
        try {
          chartRef.current.remove();
        } catch (error) {
          console.warn('Error during cleanup:', error);
        }
        chartRef.current = null;
      }
      setIsLoading(false);
    };
  }, [ticker, scriptLoaded]);

  if (!scriptLoaded) {
    return (
      <div className="bg-gray-900 border border-white/20 rounded-lg p-4">
        
        <div className="flex items-center justify-center h-[400px] text-white/50">
          <div className="text-center">
            <div className="loading loading-spinner loading-lg mb-4"></div>
            <p>Loading TradingView...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-black border border-white rounded-lg p-4">
      <div className="mb-4">
        <h3 className="text-white text-lg font-semibold">
          {ticker ? `${ticker}` : 'Select a stock to view chart'}
        </h3>
        {ticker && isLoading && (
          <p className="text-white/60 text-sm mt-1">Loading chart data...</p>
        )}
      </div>
      
      <div className="relative">
        {isLoading && ticker && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900/80 rounded-lg z-10">
            <div className="text-center text-white">
              <div className="loading loading-spinner loading-lg mb-2"></div>
              <p className="text-sm">Loading {ticker} chart...</p>
            </div>
          </div>
        )}
        
        <div 
          ref={chartContainerRef}
          className="w-full h-[400px] rounded-lg overflow-hidden bg-gray-800"
          style={{ minHeight: '400px' }}
        />
        
        {!ticker && (
          <div className="absolute inset-0 flex items-center justify-center text-white/50">
            <p>Please select a ticker symbol to display the chart</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockChart;