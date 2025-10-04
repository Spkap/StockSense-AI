import axios from 'axios';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;


console.log('Protocol mismatch warning:', window.location.protocol === 'https:' && API_BASE_URL.startsWith('http:'));

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('firebase_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log the request URL for debugging
    console.log('Making HTTP request to:', `${config.baseURL}${config.url}`);
    
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
    console.error('Error details:', {
      url: error.config?.url,
      baseURL: error.config?.baseURL,
      status: error.response?.status,
      message: error.message
    });
    
    // If token is invalid, clear it
    if (error.response?.status === 401) {
      localStorage.removeItem('firebase_token');
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;