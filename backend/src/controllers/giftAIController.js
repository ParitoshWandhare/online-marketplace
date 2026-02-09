// backend/src/controllers/giftAIController.js
/**
 * Gift AI Controller - Complete Implementation
 * Handles all Gift AI service endpoints
 */

const giftAIService = require("../services/giftAIService");
const Artwork = require("../models/Artwork");

// ========================================================================
// HELPER FUNCTIONS
// ========================================================================

/**
 * Enrich AI bundles with full artwork data from MongoDB
 */
async function enrichBundlesWithArtworkData(bundles) {
  if (!bundles || !Array.isArray(bundles) || bundles.length === 0) {
    return {
      bundles: [],
      stats: { 
        total_items: 0, 
        found_items: 0, 
        missing_items: 0,
        bundles_created: 0 
      },
      warnings: []
    };
  }

  const enriched = [];
  const warnings = [];
  const stats = {
    total_items: 0,
    found_items: 0,
    missing_items: 0,
    bundles_created: 0
  };

  for (const bundle of bundles) {
    const enrichedItems = [];
    const bundleName = bundle.bundle_name || bundle.name || 'Unnamed Bundle';

    if (!bundle.items || !Array.isArray(bundle.items) || bundle.items.length === 0) {
      warnings.push(`Bundle "${bundleName}" has no items - skipping`);
      continue;
    }

    for (const item of bundle.items) {
      stats.total_items++;
      
      try {
        let artwork = null;

        // Strategy 1: Find by mongo_id
        if (item.mongo_id) {
          try {
            artwork = await Artwork.findById(item.mongo_id)
              .populate("artistId", "name email avatarUrl");
          } catch (err) {
            console.warn(`⚠️ Invalid mongo_id: ${item.mongo_id}`);
          }
        }

        // Strategy 2: Find by exact title
        if (!artwork && item.title) {
          artwork = await Artwork.findOne({
            title: item.title,
            status: "published"
          }).populate("artistId", "name email avatarUrl");
        }

        // Strategy 3: Case-insensitive match
        if (!artwork && item.title) {
          artwork = await Artwork.findOne({
            title: new RegExp(`^${escapeRegex(item.title)}$`, 'i'),
            status: "published"
          }).populate("artistId", "name email avatarUrl");
        }

        if (artwork) {
          stats.found_items++;
          enrichedItems.push({
            mongo_id: artwork._id.toString(),
            title: artwork.title,
            reason: item.reason || "Recommended for you",
            price: artwork.price,
            currency: artwork.currency || "INR",
            artwork: {
              _id: artwork._id,
              title: artwork.title,
              description: artwork.description,
              price: artwork.price,
              currency: artwork.currency,
              quantity: artwork.quantity,
              status: artwork.status,
              tags: artwork.tags || [],
              media: artwork.media || [],
              likeCount: artwork.likeCount || 0,
              artistId: artwork.artistId,
              createdAt: artwork.createdAt
            }
          });
        } else {
          stats.missing_items++;
          const identifier = item.title || item.mongo_id || 'unknown';
          warnings.push(`Artwork not found: "${identifier}"`);
        }
      } catch (error) {
        stats.missing_items++;
        const identifier = item.title || item.mongo_id || 'unknown';
        warnings.push(`Error processing: "${identifier}" - ${error.message}`);
      }
    }

    if (enrichedItems.length > 0) {
      const totalPrice = enrichedItems.reduce(
        (sum, item) => sum + (item.price || 0),
        0
      );

      enriched.push({
        ...bundle,
        items: enrichedItems,
        total_price: totalPrice,
        item_count: enrichedItems.length,
        original_item_count: bundle.items.length
      });
      
      stats.bundles_created++;
    } else {
      warnings.push(`Bundle "${bundleName}" excluded - no valid items found`);
    }
  }

  return {
    bundles: enriched,
    stats,
    warnings: warnings.length > 0 ? warnings : undefined
  };
}

function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ========================================================================
// CONTROLLER METHODS
// ========================================================================

/**
 * Health check for AI services
 * GET /api/v1/gift-ai/health
 */
exports.healthCheck = async (req, res) => {
  try {
    const isHealthy = await giftAIService.isServiceHealthy();
    
    if (isHealthy) {
      res.json({
        success: true,
        status: "healthy",
        service: "gift-ai",
        timestamp: new Date().toISOString()
      });
    } else {
      res.status(503).json({
        success: false,
        status: "unhealthy",
        service: "gift-ai",
        message: "AI service is not responding",
        timestamp: new Date().toISOString()
      });
    }
  } catch (error) {
    console.error("Health check error:", error);
    res.status(503).json({
      success: false,
      status: "error",
      message: "Failed to check service health",
      error: error.message,
    });
  }
};

/**
 * Generate gift bundle from image
 * POST /api/v1/gift-ai/generate-bundle
 */
exports.generateGiftBundle = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    console.log(`📸 Processing image: ${req.file.originalname} (${req.file.size} bytes)`);

    // Call AI service
    const result = await giftAIService.generateGiftBundle(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to generate gift bundle",
        error: result.error,
        details: result.details
      });
    }

    // Enrich bundles with full artwork data
    const enrichedBundles = await enrichBundlesWithArtworkData(result.data.bundles);

    res.json({
      success: true,
      bundle_id: result.data.bundle_id,
      vision: result.data.vision,
      intent: result.data.intent,
      bundles: enrichedBundles.bundles,
      metadata: {
        ...result.data.metadata,
        enrichment_stats: enrichedBundles.stats
      },
      warnings: enrichedBundles.warnings
    });

  } catch (error) {
    console.error("Gift bundle generation error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during gift bundle generation",
      error: error.message,
    });
  }
};

/**
 * Search similar gifts by text query
 * GET /api/v1/gift-ai/search?query=...&limit=10
 * POST /api/v1/gift-ai/search_similar_gifts
 */
exports.searchSimilarGifts = async (req, res) => {
  try {
    const query = req.query.query || req.body.query;
    const limit = parseInt(req.query.limit || req.body.limit || "10");

    if (!query) {
      return res.status(400).json({
        success: false,
        message: "Query parameter is required",
      });
    }

    console.log(`🔍 Searching gifts: "${query}" (limit: ${limit})`);

    // Call AI service
    const result = await giftAIService.searchSimilarGifts(query, limit);

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to search gifts",
        error: result.error,
      });
    }

    // Enrich bundles with full artwork data
    const enrichedBundles = await enrichBundlesWithArtworkData(result.data.bundles);

    res.json({
      success: true,
      query: result.data.query || query,
      bundles: enrichedBundles.bundles,
      metadata: {
        ...result.data.metadata,
        enrichment_stats: enrichedBundles.stats
      },
      warnings: enrichedBundles.warnings
    });

  } catch (error) {
    console.error("Gift search error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during gift search",
      error: error.message,
    });
  }
};

// ========================================================================
// VISION AI ENDPOINTS
// ========================================================================

/**
 * Analyze craft type
 * POST /api/v1/gift-ai/analyze-craft
 */
exports.analyzeCraft = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.analyzeCraft(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to analyze craft",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Craft analysis error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during craft analysis",
      error: error.message,
    });
  }
};

/**
 * Analyze quality
 * POST /api/v1/gift-ai/analyze-quality
 */
exports.analyzeQuality = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.analyzeQuality(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to analyze quality",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Quality analysis error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during quality analysis",
      error: error.message,
    });
  }
};

/**
 * Estimate price
 * POST /api/v1/gift-ai/estimate-price
 */
exports.estimatePrice = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.estimatePrice(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to estimate price",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Price estimation error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during price estimation",
      error: error.message,
    });
  }
};

/**
 * Detect fraud
 * POST /api/v1/gift-ai/detect-fraud
 */
exports.detectFraud = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.detectFraud(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to detect fraud",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Fraud detection error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during fraud detection",
      error: error.message,
    });
  }
};

/**
 * Detect occasion
 * POST /api/v1/gift-ai/detect-occasion
 */
exports.detectOccasion = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.detectOccasion(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to detect occasion",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Occasion detection error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during occasion detection",
      error: error.message,
    });
  }
};

/**
 * Suggest packaging
 * POST /api/v1/gift-ai/suggest-packaging
 */
exports.suggestPackaging = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.suggestPackaging(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to suggest packaging",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Packaging suggestion error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during packaging suggestion",
      error: error.message,
    });
  }
};

/**
 * Detect material
 * POST /api/v1/gift-ai/detect-material
 */
exports.detectMaterial = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.detectMaterial(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to detect material",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Material detection error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during material detection",
      error: error.message,
    });
  }
};

/**
 * Analyze sentiment
 * POST /api/v1/gift-ai/analyze-sentiment
 */
exports.analyzeSentiment = async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    const result = await giftAIService.analyzeSentiment(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to analyze sentiment",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Sentiment analysis error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during sentiment analysis",
      error: error.message,
    });
  }
};

// ========================================================================
// ADMIN ENDPOINTS
// ========================================================================

/**
 * Refresh vector store
 * POST /api/v1/gift-ai/refresh-vector-store
 */
exports.refreshVectorStore = async (req, res) => {
  try {
    console.log("🔄 Refreshing vector store...");

    const result = await giftAIService.refreshVectorStore();

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to refresh vector store",
        error: result.error,
      });
    }

    res.json({
      success: true,
      message: "Vector store refreshed successfully",
      data: result.data,
    });

  } catch (error) {
    console.error("Vector store refresh error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during vector store refresh",
      error: error.message,
    });
  }
};

/**
 * Get vector store info
 * GET /api/v1/gift-ai/vector-store-info
 */
exports.getVectorStoreInfo = async (req, res) => {
  try {
    const result = await giftAIService.getVectorStoreInfo();

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to get vector store info",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });

  } catch (error) {
    console.error("Vector store info error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching vector store info",
      error: error.message,
    });
  }
};

/**
 * Index a single artwork
 * POST /api/v1/gift-ai/index-artwork/:artworkId
 */
exports.indexArtwork = async (req, res) => {
  try {
    const { artworkId } = req.params;

    // Fetch artwork from database
    const artwork = await Artwork.findById(artworkId);

    if (!artwork) {
      return res.status(404).json({
        success: false,
        message: "Artwork not found",
      });
    }

    // Index in AI service
    const result = await giftAIService.indexArtwork(artwork);

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Failed to index artwork",
        error: result.error,
      });
    }

    res.json({
      success: true,
      message: "Artwork indexed successfully",
      artwork_id: artworkId,
      data: result.data,
    });

  } catch (error) {
    console.error("Artwork indexing error:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error during artwork indexing",
      error: error.message,
    });
  }
};