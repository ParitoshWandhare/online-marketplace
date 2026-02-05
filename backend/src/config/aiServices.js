// // backend/src/config/aiServices.js
// module.exports = {
//   visionAI: {
//     baseURL: process.env.VISION_AI_SERVICE_URL || process.env.AI_SERVICES_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net",
//     apiKey: process.env.AI_SERVICE_KEY || "",
//   }
// };


// backend/src/config/aiServices.js

module.exports = {
  visionAI: {
    baseURL: process.env.GIFT_AI_SERVICE_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net",
    apiKey: process.env.AI_SERVICE_KEY || "",
    timeout: 120000, // 2 minutes
  },
  giftAI: {
    baseURL: process.env.GIFT_AI_SERVICE_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net",
    apiKey: process.env.AI_SERVICE_KEY || "",
    timeout: 180000, // 3 minutes
  }
};