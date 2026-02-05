// API Configuration
// Using environment variables with fallbacks

export const API_CONFIG = {
  // Backend API Base URL
  BASE_URL: import.meta.env.VITE_API_BASE_URL || 'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1',
  
  // Gift AI Service URL (through backend) - FIXED: Proper fallback chain
  GIFT_AI_URL: import.meta.env.VITE_GIFT_AI_API_URL || 
               import.meta.env.VITE_GIFT_AI_SERVICE_URL || 
               import.meta.env.VITE_API_BASE_URL + '/gift-ai' ||
               'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1/gift-ai',
  
  // Other service URLs
  RAZORPAY_KEY_ID: import.meta.env.VITE_RAZORPAY_KEY_ID || 'rzp_test_FL1169YIzBHiMi',
  
  // Timeouts
  DEFAULT_TIMEOUT: 30000,
  UPLOAD_TIMEOUT: 180000,
  ADMIN_TIMEOUT: 300000,
};

// Environment detection
export const isDevelopment = import.meta.env.DEV;
export const isProduction = import.meta.env.PROD;

// Log configuration with better debugging
console.log('🔧 API Configuration loaded:', {
  BASE_URL: API_CONFIG.BASE_URL,
  GIFT_AI_URL: API_CONFIG.GIFT_AI_URL,
  RAZORPAY_KEY_ID: API_CONFIG.RAZORPAY_KEY_ID ? 'SET' : 'MISSING',
  isDevelopment,
  isProduction,
});

// Debug environment variables
console.log('🔍 Environment Variables Debug:', {
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL || 'undefined',
  VITE_GIFT_AI_API_URL: import.meta.env.VITE_GIFT_AI_API_URL || 'undefined',
  VITE_GIFT_AI_SERVICE_URL: import.meta.env.VITE_GIFT_AI_SERVICE_URL || 'undefined',
  VITE_RAZORPAY_KEY_ID: import.meta.env.VITE_RAZORPAY_KEY_ID ? 'SET' : 'undefined',
});