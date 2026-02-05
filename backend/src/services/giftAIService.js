// // backend/src/services/giftAIService.js
// const axios = require("axios");
// const FormData = require("form-data");
// const fs = require("fs");

// // AI Service URLs from environment variables
// const GIFT_AI_BASE_URL = process.env.GIFT_AI_SERVICE_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net";
// //const VISION_AI_BASE_URL = process.env.VISION_AI_SERVICE_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net";

// // Timeout configuration
// const AI_REQUEST_TIMEOUT = 1200000; // 120 seconds

// /**
//  * Gift AI Service Client
//  * Handles communication with Gift AI microservices
//  */
// class GiftAIService {
//   constructor() {
//     this.giftClient = axios.create({
//       baseURL: GIFT_AI_BASE_URL,
//       timeout: AI_REQUEST_TIMEOUT,
//       headers: { "Content-Type": "application/json" },
//     });GIFT_AI_BASE_URL

//     this.visionClient = axios.create({
//       baseURL: GIFT_AI_BASE_URL,
//       timeout: AI_REQUEST_TIMEOUT,
//     });
//   }

//   // ========================================================================
//   // MAIN AI SERVICE (port 8001)
//   // ========================================================================

//   /**
//    * Generate gift bundle from image
//    * @param {Buffer} imageBuffer - Image file buffer
//    * @param {string} filename - Original filename
//    * @returns {Promise<Object>} Bundle data
//    */
//   async generateGiftBundle(imageBuffer, filename) {
//     try {
//       const formData = new FormData();
//       formData.append("image", imageBuffer, {
//         filename: filename,
//         contentType: "image/jpeg",
//       });

//       const response = await this.giftClient.post(
//         "/generate_gift_bundle",
//         formData,
//         {
//           headers: formData.getHeaders(),
//           timeout: 1800000, // 180 seconds for image processing
//         }
//       );

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       console.error("Gift bundle generation failed:", error.message);
//       return {
//         success: false,
//         error: error.response?.data?.detail || error.message,
//       };
//     }
//   }

//   /**
//    * Search similar gifts by text query
//    * @param {string} query - Search query
//    * @param {number} limit - Number of results
//    * @returns {Promise<Object>} Search results
//    */
//   async searchSimilarGifts(query, limit = 10) {
//     try {
//       const response = await this.giftClient.post(
//         "/search_similar_gifts",
//         null,
//         {
//           params: { query, limit },
//         }
//       );

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       console.error("Gift search failed:", error.message);
//       return {
//         success: false,
//         error: error.response?.data?.detail || error.message,
//       };
//     }
//   }

//   /**
//    * Index a single artwork into vector store
//    * @param {Object} artwork - Artwork object from MongoDB
//    * @returns {Promise<Object>} Index result
//    */
//   async indexArtwork(artwork) {
//     try {
//       const payload = {
//         mongo_id: artwork._id.toString(),
//         title: artwork.title,
//         description: artwork.description || "",
//         category: artwork.tags?.[0] || "General",
//         price: artwork.price,
//         tags: artwork.tags || [],
//       };

//       const response = await this.giftClient.post("/index_artwork", payload);

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       console.error("Artwork indexing failed:", error.message);
//       return {
//         success: false,
//         error: error.response?.data?.detail || error.message,
//       };
//     }
//   }

//   /**
//    * Refresh entire vector store (Admin only)
//    * @returns {Promise<Object>} Refresh result
//    */
//   async refreshVectorStore() {
//     try {
//       const response = await this.giftClient.post("/refresh_vector_store", {
//         timeout: 300000, // 5 minutes
//       });

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       console.error("Vector store refresh failed:", error.message);
//       return {
//         success: false,
//         error: error.response?.data?.detail || error.message,
//       };
//     }
//   }

//   /**
//    * Get vector store information
//    * @returns {Promise<Object>} Vector store info
//    */
//   async getVectorStoreInfo() {
//     try {
//       const response = await this.giftClient.get("/vector_store_info");

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       console.error("Vector store info fetch failed:", error.message);
//       return {
//         success: false,
//         error: error.response?.data?.detail || error.message,
//       };
//     }
//   }

//   // ========================================================================
//   // VISION AI SERVICE (port 8004)
//   // ========================================================================

//   /**
//    * Analyze craft type from image
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Craft analysis
//    */
//   async analyzeCraft(imageBuffer, filename) {
//     return this._callVisionEndpoint("/analyze_craft", imageBuffer, filename);
//   }

//   /**
//    * Analyze quality and craftsmanship
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Quality analysis
//    */
//   async analyzeQuality(imageBuffer, filename) {
//     return this._callVisionEndpoint("/analyze_quality", imageBuffer, filename);
//   }

//   /**
//    * Estimate price from image
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Price estimation
//    */
//   async estimatePrice(imageBuffer, filename) {
//     return this._callVisionEndpoint("/estimate_price", imageBuffer, filename);
//   }

//   /**
//    * Detect fraud indicators
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Fraud detection result
//    */
//   async detectFraud(imageBuffer, filename) {
//     return this._callVisionEndpoint("/detect_fraud", imageBuffer, filename);
//   }

//   /**
//    * Suggest packaging
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Packaging suggestions
//    */
//   async suggestPackaging(imageBuffer, filename) {
//     return this._callVisionEndpoint(
//       "/suggest_packaging",
//       imageBuffer,
//       filename
//     );
//   }

//   /**
//    * Detect material
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Material detection
//    */
//   async detectMaterial(imageBuffer, filename) {
//     return this._callVisionEndpoint("/detect_material", imageBuffer, filename);
//   }

//   /**
//    * Analyze sentiment
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Sentiment analysis
//    */
//   async analyzeSentiment(imageBuffer, filename) {
//     return this._callVisionEndpoint(
//       "/analyze_sentiment",
//       imageBuffer,
//       filename
//     );
//   }

//   /**
//    * Detect suitable occasion
//    * @param {Buffer} imageBuffer - Image buffer
//    * @param {string} filename - Filename
//    * @returns {Promise<Object>} Occasion detection
//    */
//   async detectOccasion(imageBuffer, filename) {
//     return this._callVisionEndpoint("/detect_occasion", imageBuffer, filename);
//   }

//   /**
//    * Generic vision endpoint caller
//    * @private
//    */
//   async _callVisionEndpoint(endpoint, imageBuffer, filename) {
//     try {
//       const formData = new FormData();
//       formData.append("image", imageBuffer, {
//         filename: filename,
//         contentType: "image/jpeg",
//       });

//       const response = await this.visionClient.post(endpoint, formData, {
//         headers: formData.getHeaders(),
//       });

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       console.error(`Vision AI ${endpoint} failed:`, error.message);
//       return {
//         success: false,
//         error: error.response?.data?.detail || error.message,
//       };
//     }
//   }

//   // ========================================================================
//   // HEALTH CHECKS
//   // ========================================================================

//   /**
//    * Check if Gift AI service is healthy
//    * @returns {Promise<boolean>}
//    */
//   async isGiftServiceHealthy() {
//     try {
//       const response = await this.giftClient.get("/health");
//       return response.status === 200;
//     } catch (error) {
//       return false;
//     }
//   }

//   /**
//    * Check if Vision AI service is healthy
//    * @returns {Promise<boolean>}
//    */
//   async isVisionServiceHealthy() {
//     try {
//       const response = await this.visionClient.get("/health");
//       return response.status === 200;
//     } catch (error) {
//       return false;
//     }
//   }
// }

// // Export singleton instance
// module.exports = new GiftAIService();



// backend/src/services/giftAIService.js

const axios = require("axios");
const FormData = require("form-data");

// FIXED: Use correct service URL
const GIFT_AI_BASE_URL = process.env.GIFT_AI_SERVICE_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net";

// Increased timeout for AI processing
const AI_REQUEST_TIMEOUT = 120000; // 120 seconds

class GiftAIService {
  constructor() {
    console.log(`🎁 Initializing Gift AI Service: ${GIFT_AI_BASE_URL}`);
    
    this.giftClient = axios.create({
      baseURL: GIFT_AI_BASE_URL,
      timeout: AI_REQUEST_TIMEOUT,
      headers: { "Content-Type": "application/json" },
    });

    this.visionClient = axios.create({
      baseURL: GIFT_AI_BASE_URL,
      timeout: AI_REQUEST_TIMEOUT,
    });

    // Add response interceptor for better error handling
    this.giftClient.interceptors.response.use(
      response => response,
      error => {
        console.error('Gift AI Client Error:', {
          url: error.config?.url,
          status: error.response?.status,
          data: error.response?.data
        });
        return Promise.reject(error);
      }
    );
  }

  /**
   * Generate gift bundle from image
   */
  async generateGiftBundle(imageBuffer, filename) {
    try {
      const formData = new FormData();
      formData.append("image", imageBuffer, {
        filename: filename,
        contentType: "image/jpeg",
      });

      console.log(`📤 Sending gift bundle request...`);

      const response = await this.giftClient.post(
        "/generate_gift_bundle",
        formData,
        {
          headers: formData.getHeaders(),
          timeout: 180000, // 3 minutes for image processing
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        }
      );

      console.log(`✅ Gift bundle generated successfully`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message;
      console.error("❌ Gift bundle generation failed:", errorMsg);
      
      return {
        success: false,
        error: errorMsg,
        details: {
          status: error.response?.status,
          url: error.config?.url,
        }
      };
    }
  }

  /**
   * Search similar gifts by text query
   */
  async searchSimilarGifts(query, limit = 10) {
    try {
      console.log(`🔍 Searching gifts: "${query}" (limit: ${limit})`);

      const response = await this.giftClient.post(
        "/search_similar_gifts",
        null,
        {
          params: { query, limit },
        }
      );

      console.log(`✅ Search completed: ${response.data?.bundles?.length || 0} bundles found`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      console.error("❌ Gift search failed:", errorMsg);
      
      return {
        success: false,
        error: errorMsg,
      };
    }
  }

  /**
   * Index a single artwork into vector store
   */
  async indexArtwork(artwork) {
    try {
      const payload = {
        mongo_id: artwork._id.toString(),
        title: artwork.title,
        description: artwork.description || "",
        category: artwork.tags?.[0] || "General",
        price: artwork.price,
        tags: artwork.tags || [],
      };

      console.log(`📇 Indexing artwork: ${payload.title} (${payload.mongo_id})`);

      const response = await this.giftClient.post("/index_artwork", payload);

      console.log(`✅ Artwork indexed successfully`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      console.error("❌ Artwork indexing failed:", errorMsg);
      
      return {
        success: false,
        error: errorMsg,
      };
    }
  }

  /**
   * Vision AI endpoints
   */
  async analyzeCraft(imageBuffer, filename) {
    return this._callVisionEndpoint("/analyze_craft", imageBuffer, filename);
  }

  async analyzeQuality(imageBuffer, filename) {
    return this._callVisionEndpoint("/analyze_quality", imageBuffer, filename);
  }

  async estimatePrice(imageBuffer, filename) {
    return this._callVisionEndpoint("/estimate_price", imageBuffer, filename);
  }

  async detectFraud(imageBuffer, filename) {
    return this._callVisionEndpoint("/detect_fraud", imageBuffer, filename);
  }

  async detectOccasion(imageBuffer, filename) {
    return this._callVisionEndpoint("/detect_occasion", imageBuffer, filename);
  }

  /**
   * Generic vision endpoint caller
   */
  async _callVisionEndpoint(endpoint, imageBuffer, filename) {
    try {
      const formData = new FormData();
      formData.append("image", imageBuffer, {
        filename: filename,
        contentType: "image/jpeg",
      });

      console.log(`👁️ Calling vision endpoint: ${endpoint}`);

      const response = await this.visionClient.post(endpoint, formData, {
        headers: formData.getHeaders(),
        timeout: 90000, // 90 seconds
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
      });

      console.log(`✅ Vision AI response from ${endpoint}`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      console.error(`❌ Vision AI ${endpoint} failed:`, errorMsg);
      
      return {
        success: false,
        error: errorMsg,
      };
    }
  }

  /**
   * Health checks
   */
  async isGiftServiceHealthy() {
    try {
      const response = await this.giftClient.get("/health", { timeout: 5000 });
      return response.status === 200;
    } catch (error) {
      console.error('Gift service health check failed:', error.message);
      return false;
    }
  }

  async isVisionServiceHealthy() {
    try {
      const response = await this.visionClient.get("/health", { timeout: 5000 });
      return response.status === 200;
    } catch (error) {
      console.error('Vision service health check failed:', error.message);
      return false;
    }
  }
}

// Export singleton instance
module.exports = new GiftAIService();