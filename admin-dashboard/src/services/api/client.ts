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
// Optional: Add request interceptor for Auth tokens if required by Phase 2/3
// Optional: Add request interceptor for Auth tokens if required by Phase 2/3
apiClient.interceptors.request.use(
  (config) => {
    // Updated to use the correct key name from your storage
    const storageKey = 'admin-auth-storage'; 
    const authStorageStr = localStorage.getItem(storageKey);
    
    if (authStorageStr) {
      try {
        const authData = JSON.parse(authStorageStr);
        
        // Ensure this matches the structure inside your 'admin-auth-storage'
        const token = authData?.state?.accessToken || authData?.accessToken;
        
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (error) {
        console.error('Failed to parse auth token:', error);
      }
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