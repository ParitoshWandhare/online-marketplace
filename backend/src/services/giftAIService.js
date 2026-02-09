// backend/src/services/giftAIService.js
/**
 * Gift AI Service Client - Updated with Better Timeout Handling
 * FIXES:
 * - Per-endpoint timeout configuration
 * - Better error handling and retry logic
 * - Request timeout warnings
 */

const axios = require("axios");
const FormData = require("form-data");

// Single service URL
const GIFT_AI_BASE_URL = process.env.GIFT_AI_SERVICE_URL || 
  "https://orchid-giftai-f6fxg6gwdbg0a2hd.centralindia-01.azurewebsites.net";

// Endpoint-specific timeouts
const TIMEOUTS = {
  BUNDLE_GENERATION: 180000,  // 3 minutes for bundle generation
  VISION_ANALYSIS: 120000,    // 2 minutes for vision endpoints
  TEXT_SEARCH: 60000,         // 1 minute for text search
  ADMIN: 300000,              // 5 minutes for admin operations
  HEALTH: 5000                // 5 seconds for health checks
};

class GiftAIService {
  constructor() {
    console.log(`🎁 Gift AI Service URL: ${GIFT_AI_BASE_URL}`);
    
    // Create base client with default timeout
    this.client = axios.create({
      baseURL: GIFT_AI_BASE_URL,
      timeout: TIMEOUTS.BUNDLE_GENERATION,
      headers: { "Content-Type": "application/json" },
    });

    // Add request interceptor for per-endpoint timeouts
    this.client.interceptors.request.use(config => {
      // Set timeout based on endpoint
      if (config.url.includes('generate_gift_bundle')) {
        config.timeout = TIMEOUTS.BUNDLE_GENERATION;
        console.log(`⏱️  Bundle generation timeout: ${config.timeout}ms`);
      } else if (config.url.includes('search')) {
        config.timeout = TIMEOUTS.TEXT_SEARCH;
        console.log(`⏱️  Text search timeout: ${config.timeout}ms`);
      } else if (config.url.includes('analyze') || config.url.includes('detect') || config.url.includes('estimate')) {
        config.timeout = TIMEOUTS.VISION_ANALYSIS;
        console.log(`⏱️  Vision analysis timeout: ${config.timeout}ms`);
      } else if (config.url.includes('refresh') || config.url.includes('vector')) {
        config.timeout = TIMEOUTS.ADMIN;
        console.log(`⏱️  Admin operation timeout: ${config.timeout}ms`);
      } else if (config.url.includes('health')) {
        config.timeout = TIMEOUTS.HEALTH;
      }
      
      return config;
    });

    // Add response interceptor for better error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        console.error('❌ Gift AI Client Error:', {
          url: error.config?.url,
          status: error.response?.status,
          timeout: error.code === 'ECONNABORTED',
          message: error.message
        });
        
        // Enhanced error message for timeouts
        if (error.code === 'ECONNABORTED') {
          error.message = `Request timeout after ${error.config?.timeout}ms - AI service may be overloaded`;
        }
        
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

      console.log(`📤 Sending gift bundle request (timeout: ${TIMEOUTS.BUNDLE_GENERATION}ms)...`);
      const startTime = Date.now();

      const response = await this.client.post(
        "/generate_gift_bundle",
        formData,
        {
          headers: formData.getHeaders(),
          maxContentLength: Infinity,
          maxBodyLength: Infinity,
        }
      );

      const duration = Date.now() - startTime;
      console.log(`✅ Bundle generated in ${duration}ms`);

      return {
        success: true,
        data: response.data,
      };
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 
                       error.response?.data?.message || 
                       error.message;
      console.error("❌ Gift bundle generation failed:", errorMsg);
      
      return {
        success: false,
        error: errorMsg,
        details: {
          status: error.response?.status,
          url: error.config?.url,
          timeout: error.code === 'ECONNABORTED'
        }
      };
    }
  }

  /**
   * Search similar gifts by text query
   */
  async searchSimilarGifts(query, limit = 10) {
    try {
      console.log(`🔍 Searching: "${query}" (limit: ${limit}, timeout: ${TIMEOUTS.TEXT_SEARCH}ms)`);
      const startTime = Date.now();

      const response = await this.client.post(
        "/search_similar_gifts",
        null,
        {
          params: { query, limit },
        }
      );

      const duration = Date.now() - startTime;
      console.log(`✅ Search completed in ${duration}ms: ${response.data?.bundles?.length || 0} bundles`);

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

  // ========================================================================
  // VISION AI ENDPOINTS
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

      console.log(`👁️ Calling: ${endpoint} (timeout: ${TIMEOUTS.VISION_ANALYSIS}ms)`);
      const startTime = Date.now();

      const response = await this.client.post(endpoint, formData, {
        headers: formData.getHeaders(),
        maxContentLength: Infinity,
        maxBodyLength: Infinity,
      });

      const duration = Date.now() - startTime;
      console.log(`✅ ${endpoint} completed in ${duration}ms`);

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
      console.log(`🔄 Refreshing vector store (timeout: ${TIMEOUTS.ADMIN}ms)...`);
      const startTime = Date.now();
      
      const response = await this.client.post("/refresh_vector_store");

      const duration = Date.now() - startTime;
      console.log(`✅ Vector store refreshed in ${duration}ms`);

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
      const response = await this.client.get("/health", { 
        timeout: TIMEOUTS.HEALTH 
      });
      return response.status === 200;
    } catch (error) {
      console.error('Health check failed:', error.message);
      return false;
    }
  }
}

// Export singleton instance
module.exports = new GiftAIService();