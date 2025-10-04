import axios from 'axios';

// Analysis API calls (for StockSense AI)
export const analysisAPI = {
  // Analyze stock using AI
  analyzeStock: async (ticker) => {
    try {
      // Use the StockSense AI API endpoint
      const aiApiUrl = import.meta.env.VITE_AI_API_URL;
      const response = await axios.get(`${aiApiUrl}/analyze/${ticker}`);
      return response.data;
    } catch (error) {
      console.error('Analysis API Error:', error);
      if (error.response?.status === 429) {
        throw new Error('API rate limit reached. Please try again later.');
      }
      if (error.response?.status === 404) {
        throw new Error(`Stock symbol ${ticker} not found. Please verify the symbol and try again.`);
      }
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        throw new Error('AI analysis service is currently unavailable. Please try again later.');
      }
      throw new Error(error.response?.data?.detail || error.message || 'Failed to analyze stock');
    }
  },

  // Get historical analysis
  getAnalysisHistory: async (ticker, limit = 10) => {
    try {
      const aiApiUrl = import.meta.env.VITE_AI_API_URL || 'http://localhost:8001';
      const response = await axios.get(`${aiApiUrl}/analysis/history/${ticker}?limit=${limit}`);
      return response.data;
    } catch (error) {
      console.error('Analysis History API Error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get analysis history');
    }
  },

  // Get analysis status
  getAnalysisStatus: async (analysisId) => {
    try {
      const aiApiUrl = import.meta.env.VITE_AI_API_URL || 'http://localhost:8001';
      const response = await axios.get(`${aiApiUrl}/analysis/status/${analysisId}`);
      return response.data;
    } catch (error) {
      console.error('Analysis Status API Error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get analysis status');
    }
  },

  // Cancel ongoing analysis
  cancelAnalysis: async (analysisId) => {
    try {
      const aiApiUrl = import.meta.env.VITE_AI_API_URL || 'http://localhost:8001';
      const response = await axios.post(`${aiApiUrl}/analysis/cancel/${analysisId}`);
      return response.data;
    } catch (error) {
      console.error('Cancel Analysis API Error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to cancel analysis');
    }
  },

  // Get market summary analysis
  getMarketSummary: async () => {
    try {
      const aiApiUrl = import.meta.env.VITE_AI_API_URL || 'http://localhost:8001';
      const response = await axios.get(`${aiApiUrl}/market/summary`);
      return response.data;
    } catch (error) {
      console.error('Market Summary API Error:', error);
      throw new Error(error.response?.data?.detail || 'Failed to get market summary');
    }
  }
};

export default analysisAPI;