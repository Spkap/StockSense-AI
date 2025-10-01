import axios from 'axios';
import { watchlistAPI } from './watchlistAPI.js';

const BASE_URL = "https://api.marketaux.com/v1/news/all";
const API_KEY = import.meta.env.VITE_NEWS_API_KEY || "6yyYvWSSdkRBahc8YO8Uusz9zM03hea3ebrQVSuY";

// Get user's watchlist stock symbols
const getUserWatchlistSymbols = async () => {
  try {
    const watchlist = await watchlistAPI.getWatchlist();
    
    if (!watchlist || !watchlist.stocks || watchlist.stocks.length === 0) {
      console.log('No stocks found in watchlist');
      return [];
    }
    
    // Extract symbols from the watchlist stocks
    return watchlist.stocks.map(stockItem => stockItem.stock.symbol);
  } catch (error) {
    console.error('Error fetching watchlist symbols:', error);
    return [];
  }
};

// Fetch news for specific symbols
const getNewsForSymbols = async (symbols, limit = 5) => {
  try {
    if (!symbols || symbols.length === 0) {
      throw new Error('No symbols provided');
    }

    // Join symbols with comma for API
    const symbolsString = symbols.join(',');
    
    const params = {
      symbols: symbolsString,
      filter_entities: true,
      language: 'en',
      api_token: API_KEY,
      limit: limit,
      sort: 'published_on', // Sort by most recent
      sort_order: 'desc'
    };

    const response = await axios.get(BASE_URL, { params });
    
    if (response.data && response.data.data) {
      return response.data.data;
    } else {
      throw new Error('Invalid response format from news API');
    }
  } catch (error) {
    console.error('Error fetching news:', error);
    throw new Error(error.response?.data?.message || 'Failed to fetch news');
  }
};

// Main function to get news for user's watchlist
const getWatchlistNews = async (limit = 5) => {
  try {
    // Step 1: Get user's watchlist symbols
    const symbols = await getUserWatchlistSymbols();
    
    if (symbols.length === 0) {
      return {
        success: true,
        message: 'No stocks in watchlist',
        articles: [],
        symbols: []
      };
    }

    console.log('Fetching news for symbols:', symbols);

    // Step 2: Fetch news for those symbols
    const articles = await getNewsForSymbols(symbols, limit);

    return {
      success: true,
      articles: articles,
      symbols: symbols,
      totalSymbols: symbols.length,
      totalArticles: articles.length
    };
  } catch (error) {
    console.error('Error in getWatchlistNews:', error);
    return {
      success: false,
      error: error.message,
      articles: [],
      symbols: []
    };
  }
};

// Get news for specific stock symbol
const getNewsForStock = async (symbol, limit = 5) => {
  try {
    const articles = await getNewsForSymbols([symbol], limit);
    return {
      success: true,
      symbol: symbol,
      articles: articles,
      totalArticles: articles.length
    };
  } catch (error) {
    console.error(`Error fetching news for ${symbol}:`, error);
    return {
      success: false,
      symbol: symbol,
      error: error.message,
      articles: []
    };
  }
};

// Export the news API functions
export const newsAPI = {
  getUserWatchlistSymbols,
  getNewsForSymbols,
  getWatchlistNews,
  getNewsForStock
};

export default newsAPI;