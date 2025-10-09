// frontend/src/services/searchAi.ts
import apiClient from "@/lib/axios";

export interface SearchAIResponse<T = unknown> {
  success?: boolean;
  data?: T;
  error?: string;
  details?: string;
}

export const searchAiService = {
  // -----------------------------
  // Search
  // -----------------------------
  search: async <T = any>(query: object): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.post("/api/search-ai/search", query);
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Search request failed", details: err?.response?.data || err?.message };
    }
  },

  searchStats: async <T = any>(): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.get("/api/search-ai/search/stats");
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Failed to fetch search stats", details: err?.response?.data || err?.message };
    }
  },

  searchHealth: async <T = any>(): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.get("/api/search-ai/search/health");
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Search health check failed", details: err?.response?.data || err?.message };
    }
  },

  searchIndex: async <T = any>(data: { id: string; text: string; payload: any }): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.post("/api/search-ai/search/index", data);
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Indexing failed", details: err?.response?.data || err?.message };
    }
  },

  // -----------------------------
  // Cultural Search
  // -----------------------------
  searchCultural: async <T = any>(query: object): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.post("/api/search-ai/search/cultural", query);
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Cultural search failed", details: err?.response?.data || err?.message };
    }
  },

  searchCulturalCategories: async <T = any>(): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.get("/api/search-ai/search/cultural/categories");
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Failed to fetch cultural categories", details: err?.response?.data || err?.message };
    }
  },

  searchCulturalSeasonal: async <T = any>(): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.get("/api/search-ai/search/cultural/seasonal");
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Failed to fetch seasonal cultural items", details: err?.response?.data || err?.message };
    }
  },

  // -----------------------------
  // Recommendations
  // -----------------------------
  recommendationsSimilar: async <T = any>(query: object): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.post("/api/search-ai/recommendations/similar", query);
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Similar recommendations failed", details: err?.response?.data || err?.message };
    }
  },

  recommendationsHealth: async <T = any>(): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.get("/api/search-ai/recommendations/health");
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Recommendation health check failed", details: err?.response?.data || err?.message };
    }
  },

  recommendationsAnalytics: async <T = any>(): Promise<SearchAIResponse<T>> => {
    try {
      const res = await apiClient.get("/api/search-ai/recommendations/analytics");
      return { success: true, data: res.data };
    } catch (err: any) {
      return { success: false, error: "Failed to fetch recommendation analytics", details: err?.response?.data || err?.message };
    }
  },
};