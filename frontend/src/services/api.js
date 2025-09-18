import axios from 'axios';

// Backend API base URL - uses environment variable or fallback
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('firebase_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for better error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error);
    
    // If token is invalid, clear it
    if (error.response?.status === 401) {
      localStorage.removeItem('firebase_token');
    }
    
    return Promise.reject(error);
  }
);

// Auth API calls
export const authAPI = {
  // Login with Firebase ID token
  login: async (idToken) => {
    try {
      const response = await apiClient.post('/users/login/', {
        idToken: idToken
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },

  
};

// Watchlist API calls
export const watchlistAPI = {
  // Get user's single watchlist
  getWatchlist: async () => {
    try {
      const response = await apiClient.get('/watchlists/');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get watchlist');
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
  }
};

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

  // Create new stock
  createStock: async (stockData) => {
    try {
      const response = await apiClient.post('/stocks/', stockData);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to create stock');
    }
  }
};

// Analysis API calls (for StockSense AI)
export const analysisAPI = {
  // Analyze stock using AI
  analyzeStock: async (ticker) => {
    try {
      // Use the StockSense AI API endpoint
      const aiApiUrl = 'http://localhost:8000'; // StockSense AI API
      const response = await axios.get(`${aiApiUrl}/analyze/${ticker}`);
      return response.data;
    } catch (error) {
      if (error.response?.status === 429) {
        throw new Error('API rate limit reached. Please try again later.');
      }
      throw new Error(error.response?.data?.detail || 'Failed to analyze stock');
    }
  }
};

export default apiClient;
