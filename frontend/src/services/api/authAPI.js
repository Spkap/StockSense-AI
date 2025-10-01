import apiClient from './client.js';

// Auth API calls
export const authAPI = {
  login: async (idToken) => {
    try {
      const response = await apiClient.post('/users/login/', {
        idToken: idToken
      });
      console.log('Login response:', response.data);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Login failed');
    }
  },
  
  // Additional auth methods can be added here
  logout: async () => {
    try {
      // Clear local storage
      localStorage.removeItem('firebase_token');
      return { success: true };
    } catch (error) {
      throw new Error('Logout failed');
    }
  },

  // Verify token
  verifyToken: async () => {
    try {
      const response = await apiClient.get('/users/verify/');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Token verification failed');
    }
  }
};

export default authAPI;