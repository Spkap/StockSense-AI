import apiClient from './client.js';

// Watchlist API calls
export const watchlistAPI = {
  getWatchlist: async () => {
    try {
      const response = await apiClient.get('/watchlists/');
      console.log('Watchlist response:', response.data);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get watchlist');
    }
  },

  // Create a new watchlist
  createWatchlist: async (watchlistData) => {
    try {
      const response = await apiClient.post('/watchlists/', watchlistData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create watchlist');
    }
  },

  // Update watchlist
  updateWatchlist: async (watchlistId, watchlistData) => {
    try {
      const response = await apiClient.put(`/watchlists/${watchlistId}/`, watchlistData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update watchlist');
    }
  },

  // Delete watchlist
  deleteWatchlist: async (watchlistId) => {
    try {
      await apiClient.delete(`/watchlists/${watchlistId}/`);
      return { success: true };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete watchlist');
    }
  },

  // Add stock to watchlist
  addStock: async (stockData) => {
    try {
      const response = await apiClient.post('/watchlists/stocks/', stockData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to add stock to watchlist');
    }
  },

  // Remove stock from watchlist
  removeStock: async (stockId) => {
    try {
      await apiClient.delete(`/watchlists/stocks/${stockId}/`);
      return { success: true };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to remove stock from watchlist');
    }
  },

  // Get watchlist stocks
  getWatchlistStocks: async (watchlistId) => {
    try {
      const response = await apiClient.get(`/watchlists/${watchlistId}/stocks/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get watchlist stocks');
    }
  }
};

export default watchlistAPI;