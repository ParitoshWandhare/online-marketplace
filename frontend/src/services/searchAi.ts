// frontend/src/services/searchAi.ts

// For development: use proxy to avoid CORS
// For production: use direct Cloud Run URL (requires CORS setup on backend)
const USE_PROXY = import.meta.env.DEV; // true in development, false in production

const SEARCH_API_URL = USE_PROXY 
  ? "/api/v1/search"
  : (import.meta.env.VITE_SEARCH_API_URL || "https://artwork-api-529829749133.asia-south1.run.app/api/v1/search");

const RECOMMENDATIONS_API_URL = USE_PROXY
  ? "/api/v1/recommendations"
  : (import.meta.env.VITE_RECOMMENDATIONS_API_URL || "https://artwork-api-529829749133.asia-south1.run.app/api/v1/recommendations");

// Types based on your API documentation
export interface ArtworkMedia {
  url: string;
  type: string;
}

export interface Artwork {
  _id: string;
  artistId: string;
  title: string;
  description: string;
  media: ArtworkMedia[];
  price: number;
  currency: string;
  tags: string[];
  status: string;
  artistName: string;
}

export interface SearchFilters {
  artistId?: string;
  tags?: string[];
  status?: string;
}

export interface SearchResponse {
  results: Artwork[];
  total: number;
  query: string;
}

export interface RecommendationsResponse {
  recommendations: Artwork[];
  source: "artwork" | "user";
}

/**
 * Search artworks using semantic AI-powered search
 */
export async function searchArtworks(
  queryText: string,
  filters: SearchFilters = {},
  numResults: number = 20
): Promise<Artwork[]> {
  try {
    console.log(`🔍 Searching for: "${queryText}"`);
    
    const response = await fetch(SEARCH_API_URL, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query_text: queryText,
        filters,
        num_results: numResults,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("❌ Search API error:", response.status, errorText);
      throw new Error(`Search request failed: ${response.status}`);
    }

    const data: SearchResponse = await response.json();
    console.log(`✅ Found ${data.results?.length || 0} artworks`);
    return data.results || [];
  } catch (err) {
    if (err instanceof TypeError && err.message.includes('fetch')) {
      console.error("❌ CORS or Network Error - Cloud Run API may need CORS configuration");
      console.error("💡 Solution: Add CORS middleware to your FastAPI backend");
    }
    console.error("Error calling Cloud Run search API:", err);
    throw err;
  }
}

/**
 * Get personalized recommendations based on user's liked artworks
 * Falls back to general search if recommendations endpoint is unavailable
 */
export async function getRecommendationsByUser(
  userId: string,
  limit: number = 10
): Promise<Artwork[]> {
  try {
    const response = await fetch(RECOMMENDATIONS_API_URL, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: userId,
        limit,
      }),
    });

    if (!response.ok) {
      // If 404, the endpoint doesn't exist - fall back to search
      if (response.status === 404) {
        console.warn("⚠️ Recommendations endpoint not available (404), using fallback");
        return getFallbackRecommendations(limit);
      }
      
      const errorText = await response.text();
      console.error("Recommendations API error response:", errorText);
      throw new Error(`Recommendations request failed: ${response.status}`);
    }

    const data: RecommendationsResponse = await response.json();
    console.log(`✅ Received ${data.recommendations?.length || 0} recommendations`);
    return data.recommendations || [];
  } catch (err) {
    // Check if it's a network/CORS error
    if (err instanceof TypeError && (err as any).message?.includes('fetch')) {
      console.warn("⚠️ Network/CORS error for recommendations, using fallback");
    } else {
      console.error("Error fetching user recommendations:", err);
    }
    
    // Always fallback gracefully
    return getFallbackRecommendations(limit);
  }
}

/**
 * Fallback function when recommendations API is unavailable
 * Uses search with popular/trending terms
 */
async function getFallbackRecommendations(limit: number = 10): Promise<Artwork[]> {
  console.log("🔄 Loading fallback recommendations using search...");
  
  try {
    // Search for popular categories to show as recommendations
    const popularTerms = ["handmade", "home decor", "art", "craft", "traditional"];
    const randomTerm = popularTerms[Math.floor(Math.random() * popularTerms.length)];
    
    const results = await searchArtworks(randomTerm, { status: "published" }, limit);
    console.log(`✅ Fallback loaded ${results.length} artworks`);
    return results;
  } catch (err) {
    console.error("❌ Fallback recommendations also failed:", err);
    return [];
  }
}

/**
 * Get similar artworks based on a specific artwork
 */
export async function getRecommendationsByArtwork(
  artworkId: string,
  limit: number = 10
): Promise<Artwork[]> {
  try {
    const response = await fetch(RECOMMENDATIONS_API_URL, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
      },
      mode: "cors",
      body: JSON.stringify({
        artwork_id: artworkId,
        limit,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Recommendations API error response:", errorText);
      throw new Error(`Recommendations request failed: ${response.status} - ${errorText}`);
    }

    const data: RecommendationsResponse = await response.json();
    return data.recommendations || [];
  } catch (err) {
    console.error("Error fetching artwork recommendations:", err);
    throw err; // Re-throw to let the UI handle it
  }
}