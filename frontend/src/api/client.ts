import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token in requests
apiClient.interceptors.request.use(
  (config) => {
    // Get the token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
    
    // If token exists, add it to the Authorization header
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle common errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Log detailed error information
    //Added hvb @ 30/11/2025
    if(error.code == "ERR_CANCELED"){
      console.warn("Request cancelled");
    }
    else{
    console.error('API Error:', {
      url: error.config?.url,
      method: error.config?.method,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    });
  }
    // Handle 401 Unauthorized errors (token expired or invalid)
    if (error.response && error.response.status === 401) {
      // Clear the token and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth_token');
        window.location.href = '/login';
      }
    }
    
    // Handle database connection errors (typically 500 errors with specific messages)
    if (error.response && error.response.status === 500) {
      const errorData = error.response.data;
      const errorMessage = typeof errorData === 'string' ? errorData : errorData?.detail || 'Server error';
      
      // Check if it's a database connection error
      if (
        errorMessage.includes('database') || 
        errorMessage.includes('connection') ||
        errorMessage.includes('SQL') ||
        errorMessage.includes('PostgreSQL')
      ) {
        console.error('Database connection error detected:', errorMessage);
        error.isDatabaseError = true;
        error.friendlyMessage = 'Unable to connect to the database. Please try again later or contact support.';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
