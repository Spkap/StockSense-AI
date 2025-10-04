import apiClient from './client.js';


const BASE_URL = import.meta.env.VITE_STOCK_API_URL || 'https://www.alphavantage.co/query';
const API_KEY = import.meta.env.ALPHAVANTAGE_API_KEY 

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

 
  getPriceData: async (symbol, interval = '1min') => {
   try{
      const url = `${BASE_URL}&symbol=${encodeURIComponent(symbol)}&interval=${interval}&apikey=${API_KEY}`;
      const header = { 'User-Agent': 'request' };
      const response = await fetch(url, { method: 'GET', headers: header });
      const data = await response.json();
      console.log(data);
      return data;

   } catch (error) {
      console.error('Error fetching price data:', error);
      throw new Error(error.response?.data?.message || 'Failed to fetch price data');
    }
 

  }

}
export default stockAPI;