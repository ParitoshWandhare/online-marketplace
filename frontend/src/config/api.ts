// API Configuration
// This file contains hardcoded URLs since environment variables are not loading in Azure Static Web Apps

export const API_CONFIG = {
  // Backend API Base URL
  BASE_URL: 'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1',
  
  // Gift AI Service URL (through backend)
  GIFT_AI_URL: 'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1/gift-ai',
  
  // Other service URLs
  RAZORPAY_KEY_ID: 'rzp_test_FL1169YIzBHiMi',
  
  // Timeouts
  DEFAULT_TIMEOUT: 30000,
  UPLOAD_TIMEOUT: 120000,
  ADMIN_TIMEOUT: 300000,
};

// Environment detection
export const isDevelopment = import.meta.env.DEV;
export const isProduction = import.meta.env.PROD;

// Log configuration
console.log('🔧 API Configuration loaded:', {
  BASE_URL: API_CONFIG.BASE_URL,
  GIFT_AI_URL: API_CONFIG.GIFT_AI_URL,
  isDevelopment,
  isProduction,
});