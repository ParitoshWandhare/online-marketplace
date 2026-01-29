// backend/src/config/aiServices.js
module.exports = {
  visionAI: {
    baseURL: process.env.VISION_AI_SERVICE_URL || process.env.AI_SERVICES_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net",
    apiKey: process.env.AI_SERVICE_KEY || "",
  }
};
