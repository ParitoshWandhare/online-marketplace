// Environment variable validation utility
export const validateEnvironment = () => {
  const requiredVars = [
    'VITE_API_BASE_URL',
    'VITE_GIFT_AI_API_URL',
    'VITE_RAZORPAY_KEY_ID'
  ];

  const missing: string[] = [];
  const invalid: string[] = [];

  console.log('🔍 Environment Variable Check:');
  
  requiredVars.forEach(varName => {
    const value = import.meta.env[varName];
    console.log(`  ${varName}:`, value);
    
    if (!value) {
      missing.push(varName);
    } else if (value === 'undefined' || (varName.includes('URL') && !value.startsWith('http'))) {
      invalid.push(varName);
    }
  });

  if (missing.length > 0) {
    console.error('❌ Missing environment variables:', missing);
  }
  
  if (invalid.length > 0) {
    console.error('❌ Invalid environment variables:', invalid);
  }

  const isValid = missing.length === 0 && invalid.length === 0;
  console.log(isValid ? '✅ Environment validation passed' : '❌ Environment validation failed');
  
  return {
    isValid,
    missing,
    invalid
  };
};

// Auto-run validation in development
if (import.meta.env.DEV) {
  validateEnvironment();
}