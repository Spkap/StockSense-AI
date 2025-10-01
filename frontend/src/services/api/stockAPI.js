import apiClient from './client.js';

// Stock API calls
export const stockAPI = {
  // Get all stocks with optional search
  getStocks: async (search = '') => {
    try {
      const url = search ? `/stocks/?search=${encodeURIComponent(search)}` : '/stocks/';
      const response = await apiClient.get(url);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get stocks');
    }
  },

  // Get stock by ID
  getStock: async (stockId) => {
    try {
      const response = await apiClient.get(`/stocks/${stockId}/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get stock');
    }
  },

  // Get stock by symbol
  getStockBySymbol: async (symbol) => {
    try {
      const response = await apiClient.get(`/stocks/symbol/${symbol}/`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get stock by symbol');
    }
  },

  // Create new stock
  createStock: async (stockData) => {
    try {
      const response = await apiClient.post('/stocks/', stockData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create stock');
    }
  },

  // Update stock
  updateStock: async (stockId, stockData) => {
    try {
      const response = await apiClient.put(`/stocks/${stockId}/`, stockData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to update stock');
    }
  },

  // Delete stock
  deleteStock: async (stockId) => {
    try {
      await apiClient.delete(`/stocks/${stockId}/`);
      return { success: true };
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete stock');
    }
  },

  // Get stock price history
  getStockHistory: async (symbol, period = '1y') => {
    try {
      const response = await apiClient.get(`/stocks/${symbol}/history/?period=${period}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get stock history');
    }
  },

  
};

export default stockAPI;