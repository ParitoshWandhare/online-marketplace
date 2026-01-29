import axios from 'axios';

const baseURL = import.meta.env.VITE_API_BASE_URL || 'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1';

// Debug logging to see what URL is being used
console.log('🔧 API Base URL:', baseURL);
console.log('🔧 Environment VITE_API_BASE_URL:', import.meta.env.VITE_API_BASE_URL);
console.log('🔧 All environment variables:', import.meta.env);

const apiClient = axios.create({
  baseURL,
  timeout: 30000, // Increased timeout
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Enable credentials for CORS
});

// Request interceptor to add authorization token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log the request for debugging
    console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`);
    
    return config;
  },
  (error) => {
    console.error('🚫 Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for global error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.method?.toUpperCase()} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ API Error: ${error.response?.status || 'Network'} ${error.config?.method?.toUpperCase()} ${error.config?.url}`, error.response?.data || error.message);
    
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;