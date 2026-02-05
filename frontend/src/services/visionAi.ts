import apiClient from "@/lib/axios";

export interface VisionResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  details?: string;
}

/**
 * Helper to upload a single image file to Vision AI routes
 */
async function postImage<T = any>(endpoint: string, imageFile: File | Blob): Promise<VisionResponse<T>> {
  const formData = new FormData();
  formData.append("image", imageFile);

  try {
    const response = await apiClient.post(endpoint, formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 120000,
    });
    return { success: true, data: response.data };
  } catch (err: any) {
    return {
      success: false,
      error: "Vision AI request failed",
      details: err?.response?.data || err?.message || "Unknown error",
    };
  }
}

/**
 * Vision AI Service Routes
 * Matches backend routes: /api/v1/vision/*
 */
export const visionAiService = {
  async generateStory(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/generate-story", file);
  },

  async similarCrafts(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/similar-crafts", file);
  },

  async priceSuggestion(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/price-suggestion", file);
  },

  async complementaryProducts(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/complementary-products", file);
  },

  async purchaseAnalysis(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/purchase-analysis", file);
  },

  async fraudDetection(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/fraud-detection", file);
  },

  async orderFulfillment(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/order_fulfillment_analysis", file);
  },

  async qualityPredictions(file: File | Blob): Promise<VisionResponse> {
    return postImage("/vision/quality-predictions", file);
  },
};
