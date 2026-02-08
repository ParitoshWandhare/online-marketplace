// backend/src/services/giftAIService.js
/**
 * Gift AI Service Client - Updated for Unified Service
 * All endpoints now point to single deployed service
 */

const axios = require("axios");
const FormData = require("form-data");

// Single service URL
const GIFT_AI_BASE_URL = process.env.GIFT_AI_SERVICE_URL || 
  "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net";

const AI_REQUEST_TIMEOUT = 180000; // 3 minutes

class GiftAIService {
  constructor() {
    console.log(`🎁 Gift AI Service URL: ${GIFT_AI_BASE_URL}`);
    
    // Single axios client for all endpoints
    this.client = axios.create({
      baseURL: GIFT_AI_BASE_URL,
      timeout: AI_REQUEST_TIMEOUT,
      headers: { "Content-Type": "application/json" },
    });

    // Add response interceptor for better error handling
    this.client.interceptors.response.use(
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

  // ========================================================================
  // GIFT BUNDLE GENERATION
  // ========================================================================

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

      console.log(`📤 Generating gift bundle...`);

      const response = await this.client.post(
        "/generate_gift_bundle",
        formData,
        {
          headers: formData.getHeaders(),
          timeout: 180000,
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        }
      );

      console.log(`✅ Bundle generated successfully`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 
                       error.response?.data?.message || 
                       error.message;
      console.error("❌ Bundle generation failed:", errorMsg);
      
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
      console.log(`🔍 Searching: "${query}" (limit: ${limit})`);

      const response = await this.client.post(
        "/search_similar_gifts",
        null,
        {
          params: { query, limit },
        }
      );

      console.log(`✅ Search completed: ${response.data?.bundles?.length || 0} bundles`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      console.error("❌ Search failed:", errorMsg);
      
      return {
        success: false,
        error: errorMsg,
      };
    }
  }

  // ========================================================================
  // VISION AI ENDPOINTS (All from same service)
  // ========================================================================

  /**
   * Analyze craft type
   */
  async analyzeCraft(imageBuffer, filename) {
    return this._callVisionEndpoint("/analyze_craft", imageBuffer, filename);
  }

  /**
   * Analyze quality
   */
  async analyzeQuality(imageBuffer, filename) {
    return this._callVisionEndpoint("/analyze_quality", imageBuffer, filename);
  }

  /**
   * Estimate price
   */
  async estimatePrice(imageBuffer, filename) {
    return this._callVisionEndpoint("/estimate_price", imageBuffer, filename);
  }

  /**
   * Detect fraud
   */
  async detectFraud(imageBuffer, filename) {
    return this._callVisionEndpoint("/detect_fraud", imageBuffer, filename);
  }

  /**
   * Detect occasion
   */
  async detectOccasion(imageBuffer, filename) {
    return this._callVisionEndpoint("/detect_occasion", imageBuffer, filename);
  }

  /**
   * Suggest packaging
   */
  async suggestPackaging(imageBuffer, filename) {
    return this._callVisionEndpoint("/suggest_packaging", imageBuffer, filename);
  }

  /**
   * Detect material
   */
  async detectMaterial(imageBuffer, filename) {
    return this._callVisionEndpoint("/detect_material", imageBuffer, filename);
  }

  /**
   * Analyze sentiment
   */
  async analyzeSentiment(imageBuffer, filename) {
    return this._callVisionEndpoint("/analyze_sentiment", imageBuffer, filename);
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

      console.log(`👁️ Calling: ${endpoint}`);

      const response = await this.client.post(endpoint, formData, {
        headers: formData.getHeaders(),
        timeout: 90000,
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
      });

      console.log(`✅ ${endpoint} completed`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || error.message;
      console.error(`❌ ${endpoint} failed:`, errorMsg);
      
      return {
        success: false,
        error: errorMsg,
      };
    }
  }

  // ========================================================================
  // ADMIN ENDPOINTS
  // ========================================================================

  /**
   * Refresh vector store
   */
  async refreshVectorStore() {
    try {
      console.log("🔄 Refreshing vector store...");
      
      const response = await this.client.post("/refresh_vector_store", {
        timeout: 300000, // 5 minutes
      });

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error("❌ Refresh failed:", error.message);
      return {
        success: false,
        error: error.response?.data?.detail || error.message,
      };
    }
  }

  /**
   * Index a single artwork
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

      console.log(`📇 Indexing: ${payload.title}`);

      const response = await this.client.post("/index_artwork", payload);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      console.error("❌ Indexing failed:", error.message);
      return {
        success: false,
        error: error.response?.data?.detail || error.message,
      };
    }
  }

  /**
   * Get vector store info
   */
  async getVectorStoreInfo() {
    try {
      const response = await this.client.get("/vector_store_info");
      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.detail || error.message,
      };
    }
  }

  // ========================================================================
  // HEALTH CHECKS
  // ========================================================================

  /**
   * Check if service is healthy
   */
  async isServiceHealthy() {
    try {
      const response = await this.client.get("/health", { timeout: 5000 });
      return response.status === 200;
    } catch (error) {
      console.error('Health check failed:', error.message);
      return false;
    }
  }
}

// Export singleton instance
module.exports = new GiftAIService();



// // backend/src/services/giftAIService.js

// const axios = require("axios");
// const FormData = require("form-data");

// // FIXED: Use correct service URL
// const GIFT_AI_BASE_URL = process.env.GIFT_AI_SERVICE_URL || "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net";

// // Increased timeout for AI processing
// const AI_REQUEST_TIMEOUT = 120000; // 120 seconds

// class GiftAIService {
//   constructor() {
//     console.log(`🎁 Initializing Gift AI Service: ${GIFT_AI_BASE_URL}`);
    
//     this.giftClient = axios.create({
//       baseURL: GIFT_AI_BASE_URL,
//       timeout: AI_REQUEST_TIMEOUT,
//       headers: { "Content-Type": "application/json" },
//     });

//     this.visionClient = axios.create({
//       baseURL: GIFT_AI_BASE_URL,
//       timeout: AI_REQUEST_TIMEOUT,
//     });

//     // Add response interceptor for better error handling
//     this.giftClient.interceptors.response.use(
//       response => response,
//       error => {
//         console.error('Gift AI Client Error:', {
//           url: error.config?.url,
//           status: error.response?.status,
//           data: error.response?.data
//         });
//         return Promise.reject(error);
//       }
//     );
//   }

//   /**
//    * Generate gift bundle from image
//    */
//   async generateGiftBundle(imageBuffer, filename) {
//     try {
//       const formData = new FormData();
//       formData.append("image", imageBuffer, {
//         filename: filename,
//         contentType: "image/jpeg",
//       });

//       console.log(`📤 Sending gift bundle request...`);

//       const response = await this.giftClient.post(
//         "/generate_gift_bundle",
//         formData,
//         {
//           headers: formData.getHeaders(),
//           timeout: 180000, // 3 minutes for image processing
//           maxContentLength: Infinity,
//           maxBodyLength: Infinity,
//         }
//       );

//       console.log(`✅ Gift bundle generated successfully`);

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message;
//       console.error("❌ Gift bundle generation failed:", errorMsg);
      
//       return {
//         success: false,
//         error: errorMsg,
//         details: {
//           status: error.response?.status,
//           url: error.config?.url,
//         }
//       };
//     }
//   }

//   /**
//    * Search similar gifts by text query
//    */
//   async searchSimilarGifts(query, limit = 10) {
//     try {
//       console.log(`🔍 Searching gifts: "${query}" (limit: ${limit})`);

//       const response = await this.giftClient.post(
//         "/search_similar_gifts",
//         null,
//         {
//           params: { query, limit },
//         }
//       );

//       console.log(`✅ Search completed: ${response.data?.bundles?.length || 0} bundles found`);

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       const errorMsg = error.response?.data?.detail || error.message;
//       console.error("❌ Gift search failed:", errorMsg);
      
//       return {
//         success: false,
//         error: errorMsg,
//       };
//     }
//   }

//   /**
//    * Index a single artwork into vector store
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

//       console.log(`📇 Indexing artwork: ${payload.title} (${payload.mongo_id})`);

//       const response = await this.giftClient.post("/index_artwork", payload);

//       console.log(`✅ Artwork indexed successfully`);

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       const errorMsg = error.response?.data?.detail || error.message;
//       console.error("❌ Artwork indexing failed:", errorMsg);
      
//       return {
//         success: false,
//         error: errorMsg,
//       };
//     }
//   }

//   /**
//    * Vision AI endpoints
//    */
//   async analyzeCraft(imageBuffer, filename) {
//     return this._callVisionEndpoint("/analyze_craft", imageBuffer, filename);
//   }

//   async analyzeQuality(imageBuffer, filename) {
//     return this._callVisionEndpoint("/analyze_quality", imageBuffer, filename);
//   }

//   async estimatePrice(imageBuffer, filename) {
//     return this._callVisionEndpoint("/estimate_price", imageBuffer, filename);
//   }

//   async detectFraud(imageBuffer, filename) {
//     return this._callVisionEndpoint("/detect_fraud", imageBuffer, filename);
//   }

//   async detectOccasion(imageBuffer, filename) {
//     return this._callVisionEndpoint("/detect_occasion", imageBuffer, filename);
//   }

//   /**
//    * Generic vision endpoint caller
//    */
//   async _callVisionEndpoint(endpoint, imageBuffer, filename) {
//     try {
//       const formData = new FormData();
//       formData.append("image", imageBuffer, {
//         filename: filename,
//         contentType: "image/jpeg",
//       });

//       console.log(`👁️ Calling vision endpoint: ${endpoint}`);

//       const response = await this.visionClient.post(endpoint, formData, {
//         headers: formData.getHeaders(),
//         timeout: 90000, // 90 seconds
//         maxContentLength: Infinity,
//         maxBodyLength: Infinity,
//       });

//       console.log(`✅ Vision AI response from ${endpoint}`);

//       return {
//         success: true,
//         data: response.data,
//       };
//     } catch (error) {
//       const errorMsg = error.response?.data?.detail || error.message;
//       console.error(`❌ Vision AI ${endpoint} failed:`, errorMsg);
      
//       return {
//         success: false,
//         error: errorMsg,
//       };
//     }
//   }

//   /**
//    * Health checks
//    */
//   async isGiftServiceHealthy() {
//     try {
//       const response = await this.giftClient.get("/health", { timeout: 5000 });
//       return response.status === 200;
//     } catch (error) {
//       console.error('Gift service health check failed:', error.message);
//       return false;
//     }
//   }

//   async isVisionServiceHealthy() {
//     try {
//       const response = await this.visionClient.get("/health", { timeout: 5000 });
//       return response.status === 200;
//     } catch (error) {
//       console.error('Vision service health check failed:', error.message);
//       return false;
//     }
//   }
// }

// // Export singleton instance
// module.exports = new GiftAIService();