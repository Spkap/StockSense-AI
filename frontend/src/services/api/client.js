import axios from 'axios';

const API_BASE_URL = 'http://localhost:9000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});


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

export default apiClient;