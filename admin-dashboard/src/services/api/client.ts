import axios from 'axios';

// Fallback to localhost if Vite environment variables aren't injected yet
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Optional: Add request interceptor for Auth tokens if required by Phase 2/3
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('admin_token'); // Adjust key as per your auth setup
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Optional: Add response interceptor for global error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle global errors (e.g., redirecting to login on 401 Unauthorized)
    if (error.response?.status === 401) {
      console.error('Unauthorized! Redirecting or clearing session...');
    }
    return Promise.reject(error);
  }
);