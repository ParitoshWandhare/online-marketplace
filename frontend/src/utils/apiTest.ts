// Simple API configuration test
import { API_CONFIG } from '@/config/api';

export const testApiConfiguration = () => {
  console.log('🧪 Testing API Configuration...');
  
  const tests = [
    {
      name: 'BASE_URL',
      value: API_CONFIG.BASE_URL,
      expected: 'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1'
    },
    {
      name: 'GIFT_AI_URL',
      value: API_CONFIG.GIFT_AI_URL,
      expected: 'https://orchid-backend-ewfkdwcdf6g5abg2.centralindia-01.azurewebsites.net/api/v1/gift-ai'
    }
  ];

  let allPassed = true;

  tests.forEach(test => {
    const passed = test.value === test.expected;
    console.log(`${passed ? '✅' : '❌'} ${test.name}: ${test.value}`);
    if (!passed) {
      console.error(`   Expected: ${test.expected}`);
      allPassed = false;
    }
  });

  if (allPassed) {
    console.log('🎉 All API configuration tests passed!');
  } else {
    console.error('💥 Some API configuration tests failed!');
  }

  return allPassed;
};

// Auto-run in development
if (import.meta.env.DEV) {
  testApiConfiguration();
}