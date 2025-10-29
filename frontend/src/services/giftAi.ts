// src/services/giftAi.ts
import axios, { AxiosInstance, AxiosResponse } from 'axios';

const API_BASE_URL = import.meta.env.VITE_GIFT_AI_API_URL || 'http://localhost:4000/api/v1/gift-ai';

// ========================================================================
// TYPE DEFINITIONS
// ========================================================================

export interface Media {
  url: string;
  type: 'image' | 'video';
  sizeBytes: number;
  storageKey: string;
}

export interface Artist {
  _id: string;
  name: string;
  email: string;
  avatarUrl?: string;
}

export interface Artwork {
  _id: string;
  title: string;
  description?: string;
  price: number;
  currency: string;
  quantity: number;
  status: 'draft' | 'published' | 'out_of_stock' | 'removed';
  tags: string[];
  media: Media[];
  artistId: Artist | string;
  createdAt: string;
  updatedAt: string;
}

export interface BundleItem {
  mongo_id: string;
  title: string;
  price: number;
  similarity?: number;
  artwork?: Artwork; // Enriched with full MongoDB artwork data
  reason?: string;
}

export interface GiftBundle {
  bundle_id?: string;
  bundle_name?: string;
  name?: string;
  description?: string;
  theme?: string;
  total_price: number;
  items: BundleItem[];
}

export interface GenerateBundleResponse {
  success: boolean;
  message: string;
  bundle_id?: string;
  vision?: any;
  intent?: any;
  bundles: GiftBundle[];
  metadata?: any;
}

export interface SearchResponse {
  success: boolean;
  query: string;
  count: number;
  bundles: GiftBundle[];
  metadata?: any;
}

export interface VisionResponse {
  success: boolean;
  data: any;
}

export interface HealthCheckResponse {
  success: boolean;
  services: {
    gift_ai: {
      status: 'healthy' | 'unhealthy';
      url: string;
    };
    vision_ai: {
      status: 'healthy' | 'unhealthy';
      url: string;
    };
  };
  all_healthy: boolean;
}

export interface VectorStoreInfoResponse {
  success: boolean;
  data: any;
}

export interface IndexArtworkResponse {
  success: boolean;
  message: string;
  data?: any;
}

// ========================================================================
// GIFT AI SERVICE CLASS
// ========================================================================

class GiftAIService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 90000,
      withCredentials: true,
      headers: { 
        'Content-Type': 'application/json' 
      },
    });
  }

  // ========================================================================
  // PUBLIC ENDPOINTS (No Authentication Required)
  // ========================================================================

  /**
   * Health check for AI services
   * GET /api/v1/gift-ai/health
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    console.log('Checking AI services health...');
    const res: AxiosResponse<HealthCheckResponse> = await this.api.get('/health');
    console.log('Health check response:', res.data);
    return res.data;
  }

  /**
   * Generate gift bundle from uploaded image
   * POST /api/v1/gift-ai/generate-bundle
   */
  async generateGiftBundle(imageFile: File): Promise<GenerateBundleResponse> {
    const formData = new FormData();
    formData.append('image', imageFile);

    console.log('📸 Uploading image for bundle generation:', imageFile.name);
    
    const res: AxiosResponse<GenerateBundleResponse> = await this.api.post(
      '/generate-bundle',
      formData,
      {
        headers: { 
          'Content-Type': 'multipart/form-data' 
        },
        timeout: 120000, // 120 seconds for image processing
      }
    );
    
    console.log('✅ Bundle generated:', res.data);
    return res.data;
  }

  /**
   * Search similar gifts by text query
   * GET /api/v1/gift-ai/search?query=...&limit=10
   */
  async searchSimilarGifts(query: string, limit = 10): Promise<SearchResponse> {
    if (!query || query.trim().length === 0) {
      throw new Error('Search query is required');
    }

    console.log(`🔍 Searching gifts for: "${query}" (limit: ${limit})`);

    const res: AxiosResponse<SearchResponse> = await this.api.get('/search', {
      params: { 
        query: query.trim(), 
        limit 
      }
    });

    console.log('✅ Search results:', res.data);
    return res.data;
  }

  // ========================================================================
  // VISION AI ENDPOINTS
  // ========================================================================

  /**
   * Generic vision endpoint caller
   * @private
   */
  private async callVisionEndpoint(
    endpoint: string, 
    imageFile: File
  ): Promise<VisionResponse> {
    const formData = new FormData();
    formData.append('image', imageFile);

    console.log(`🔮 Vision AI → POST ${endpoint}`, imageFile.name);
    
    const res: AxiosResponse<VisionResponse> = await this.api.post(
      endpoint, 
      formData, 
      {
        headers: { 
          'Content-Type': 'multipart/form-data' 
        },
      }
    );

    console.log(`✅ ${endpoint} result:`, res.data);
    return res.data;
  }

  /**
   * Analyze craft type from image
   * POST /api/v1/gift-ai/analyze-craft
   */
  async analyzeCraft(imageFile: File): Promise<VisionResponse> {
    return this.callVisionEndpoint('/analyze-craft', imageFile);
  }

  /**
   * Analyze quality and craftsmanship
   * POST /api/v1/gift-ai/analyze-quality
   */
  async analyzeQuality(imageFile: File): Promise<VisionResponse> {
    return this.callVisionEndpoint('/analyze-quality', imageFile);
  }

  /**
   * Estimate price from image
   * POST /api/v1/gift-ai/estimate-price
   */
  async estimatePrice(imageFile: File): Promise<VisionResponse> {
    return this.callVisionEndpoint('/estimate-price', imageFile);
  }

  /**
   * Detect fraud indicators
   * POST /api/v1/gift-ai/detect-fraud
   */
  async detectFraud(imageFile: File): Promise<VisionResponse> {
    return this.callVisionEndpoint('/detect-fraud', imageFile);
  }

  /**
   * Detect suitable occasion
   * POST /api/v1/gift-ai/detect-occasion
   */
  async detectOccasion(imageFile: File): Promise<VisionResponse> {
    return this.callVisionEndpoint('/detect-occasion', imageFile);
  }

  // ========================================================================
  // ADMIN ENDPOINTS (Requires Authentication)
  // ========================================================================

  /**
   * Refresh vector store (sync MongoDB → Qdrant)
   * POST /api/v1/gift-ai/refresh-vector-store
   * Requires: Authentication
   */
  async refreshVectorStore(): Promise<any> {
    console.log('🔄 Refreshing vector store...');
    const res = await this.api.post('/refresh-vector-store', null, {
      timeout: 300000, // 5 minutes
    });
    console.log('✅ Vector store refreshed:', res.data);
    return res.data;
  }

  /**
   * Get vector store information
   * GET /api/v1/gift-ai/vector-store-info
   * Requires: Authentication
   */
  async getVectorStoreInfo(): Promise<VectorStoreInfoResponse> {
    console.log('📊 Fetching vector store info...');
    const res: AxiosResponse<VectorStoreInfoResponse> = await this.api.get(
      '/vector-store-info'
    );
    console.log('✅ Vector store info:', res.data);
    return res.data;
  }

  /**
   * Index a specific artwork into vector store
   * POST /api/v1/gift-ai/index-artwork/:artworkId
   * Requires: Authentication
   */
  async indexArtwork(artworkId: string): Promise<IndexArtworkResponse> {
    console.log(`📥 Indexing artwork: ${artworkId}`);
    const res: AxiosResponse<IndexArtworkResponse> = await this.api.post(
      `/index-artwork/${artworkId}`
    );
    console.log('✅ Artwork indexed:', res.data);
    return res.data;
  }

  // ========================================================================
  // ERROR HANDLING WRAPPER (Optional)
  // ========================================================================

  /**
   * Wrapper for better error handling
   */
  private async handleRequest<T>(
    requestFn: () => Promise<AxiosResponse<T>>
  ): Promise<T> {
    try {
      const response = await requestFn();
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorMessage = 
          error.response?.data?.message || 
          error.response?.data?.error || 
          error.message;
        
        console.error('Gift AI Service Error:', {
          status: error.response?.status,
          message: errorMessage,
          endpoint: error.config?.url,
        });
        
        throw new Error(errorMessage);
      }
      throw error;
    }
  }
}

// ========================================================================
// EXPORT SINGLETON INSTANCE
// ========================================================================

export const giftAiService = new GiftAIService();
export default giftAiService;