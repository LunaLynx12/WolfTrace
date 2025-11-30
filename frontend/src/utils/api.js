/**
 * Centralized API client with interceptors and request cancellation
 * Performance: Single axios instance with consistent error handling
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 30000, // 30 second timeout
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add AbortController for request cancellation
    if (!config.signal) {
      config.signal = new AbortController().signal;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for consistent error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle network errors
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout:', error.config.url);
    } else if (error.message === 'Network Error') {
      console.error('Network error:', error.config.url);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
export { API_BASE };

