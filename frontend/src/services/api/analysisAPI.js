import axios from 'axios';

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
  },

  // Get historical analysis
  getAnalysisHistory: async (ticker, limit = 10) => {
    try {
      const aiApiUrl = 'http://localhost:8000';
      const response = await axios.get(`${aiApiUrl}/analysis/history/${ticker}?limit=${limit}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get analysis history');
    }
  },

  // Get analysis status
  getAnalysisStatus: async (analysisId) => {
    try {
      const aiApiUrl = 'http://localhost:8000';
      const response = await axios.get(`${aiApiUrl}/analysis/status/${analysisId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get analysis status');
    }
  },

  // Cancel ongoing analysis
  cancelAnalysis: async (analysisId) => {
    try {
      const aiApiUrl = 'http://localhost:8000';
      const response = await axios.post(`${aiApiUrl}/analysis/cancel/${analysisId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to cancel analysis');
    }
  },

  // Get market summary analysis
  getMarketSummary: async () => {
    try {
      const aiApiUrl = 'http://localhost:8000';
      const response = await axios.get(`${aiApiUrl}/market/summary`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get market summary');
    }
  }
};

export default analysisAPI;