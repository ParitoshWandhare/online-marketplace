// backend/src/controllers/giftAIController.js
const giftAIService = require("../services/giftAIService");
const Artwork = require("../models/Artwork");

// ========================================================================
// GIFT BUNDLE GENERATION
// ========================================================================

/**
 * Generate gift bundle from uploaded image
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

    console.log("📸 Processing gift bundle request for:", req.file.originalname);

    // Call AI service
    const result = await giftAIService.generateGiftBundle(
      req.file.buffer,
      req.file.originalname
    );

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Gift bundle generation failed",
        error: result.error,
      });
    }

    // Enrich bundles with actual artwork data from MongoDB
    const enrichmentResult = await enrichBundlesWithArtworkData(
      result.data.bundles
    );

    res.json({
      success: true,
      message: "Gift bundle generated successfully",
      bundle_id: result.data.bundle_id,
      vision: result.data.vision,
      intent: result.data.intent,
      bundles: enrichmentResult.bundles,
      metadata: {
        ...result.data.metadata,
        enrichment_stats: enrichmentResult.stats
      },
      warnings: enrichmentResult.warnings
    });
  } catch (error) {
    console.error("Error in generateGiftBundle:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

// ========================================================================
// TEXT SEARCH FOR GIFTS
// ========================================================================

/**
 * Search similar gifts by text query
 * GET /api/v1/gift-ai/search?query=...&limit=10
 */
exports.searchSimilarGifts = async (req, res) => {
  try {
    const { query, limit } = req.query;

    if (!query || query.trim().length === 0) {
      return res.status(400).json({
        success: false,
        message: "Search query is required",
      });
    }

    const searchLimit = parseInt(limit) || 10;

    console.log(`🔍 Searching gifts for: "${query}"`);

    const result = await giftAIService.searchSimilarGifts(query, searchLimit);

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Gift search failed",
        error: result.error,
      });
    }

    // Enrich with MongoDB data
    const enrichmentResult = await enrichBundlesWithArtworkData(
      result.data.bundles
    );

    res.json({
      success: true,
      query: query,
      count: enrichmentResult.bundles.length,
      bundles: enrichmentResult.bundles,
      metadata: {
        ...result.data.metadata,
        enrichment_stats: enrichmentResult.stats
      },
      warnings: enrichmentResult.warnings
    });
  } catch (error) {
    console.error("Error in searchSimilarGifts:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

// ========================================================================
// VISION AI ENDPOINTS
// ========================================================================

/**
 * Analyze craft type from image
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
        message: "Craft analysis failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });
  } catch (error) {
    console.error("Error in analyzeCraft:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

/**
 * Analyze quality from image
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
        message: "Quality analysis failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });
  } catch (error) {
    console.error("Error in analyzeQuality:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

/**
 * Estimate price from image
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
        message: "Price estimation failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });
  } catch (error) {
    console.error("Error in estimatePrice:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

/**
 * Detect fraud indicators
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
        message: "Fraud detection failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });
  } catch (error) {
    console.error("Error in detectFraud:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

/**
 * Detect occasion from image
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
        message: "Occasion detection failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });
  } catch (error) {
    console.error("Error in detectOccasion:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

// ========================================================================
// ADMIN ENDPOINTS
// ========================================================================

/**
 * Refresh vector store (Admin only)
 * POST /api/v1/gift-ai/refresh-vector-store
 */
exports.refreshVectorStore = async (req, res) => {
  try {
    console.log("🔄 Starting vector store refresh...");

    const result = await giftAIService.refreshVectorStore();

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Vector store refresh failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      message: "Vector store refreshed successfully",
      data: result.data,
    });
  } catch (error) {
    console.error("Error in refreshVectorStore:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
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
        message: "Failed to fetch vector store info",
        error: result.error,
      });
    }

    res.json({
      success: true,
      data: result.data,
    });
  } catch (error) {
    console.error("Error in getVectorStoreInfo:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

/**
 * Index artwork when created/updated
 * POST /api/v1/gift-ai/index-artwork/:artworkId
 */
exports.indexArtwork = async (req, res) => {
  try {
    const { artworkId } = req.params;

    const artwork = await Artwork.findById(artworkId);
    if (!artwork) {
      return res.status(404).json({
        success: false,
        message: "Artwork not found",
      });
    }

    const result = await giftAIService.indexArtwork(artwork);

    if (!result.success) {
      return res.status(500).json({
        success: false,
        message: "Artwork indexing failed",
        error: result.error,
      });
    }

    res.json({
      success: true,
      message: "Artwork indexed successfully",
      data: result.data,
    });
  } catch (error) {
    console.error("Error in indexArtwork:", error);
    res.status(500).json({
      success: false,
      message: "Internal server error",
      error: error.message,
    });
  }
};

/**
 * Health check for AI services
 * GET /api/v1/gift-ai/health
 */
exports.healthCheck = async (req, res) => {
  try {
    const giftServiceHealthy = await giftAIService.isGiftServiceHealthy();
    const visionServiceHealthy = await giftAIService.isVisionServiceHealthy();

    res.json({
      success: true,
      services: {
        gift_ai: {
          status: giftServiceHealthy ? "healthy" : "unhealthy",
          url: process.env.GIFT_AI_SERVICE_URL || "http://localhost:8001",
        },
        vision_ai: {
          status: visionServiceHealthy ? "healthy" : "unhealthy",
          //url: process.env.VISION_AI_SERVICE_URL || "http://localhost:8001",
          url: process.env.GIFT_AI_SERVICE_URL || "http://localhost:8001",
        },
      },
      all_healthy: giftServiceHealthy && visionServiceHealthy,
    });
  } catch (error) {
    console.error("Error in healthCheck:", error);
    res.status(500).json({
      success: false,
      message: "Health check failed",
      error: error.message,
    });
  }
};

// ========================================================================
// HELPER FUNCTIONS
// ========================================================================

/**
 * Enrich AI bundles with full artwork data from MongoDB
 * Now includes detailed stats and warnings
 */
async function enrichBundlesWithArtworkData(bundles) {
  if (!bundles || bundles.length === 0) {
    return {
      bundles: [],
      stats: { total: 0, found: 0, missing: 0 },
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

    for (const item of bundle.items || []) {
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

        // Strategy 2: Find by exact title match
        if (!artwork && item.title) {
          artwork = await Artwork.findOne({
            title: item.title,
            status: "published"
          }).populate("artistId", "name email avatarUrl");
        }

        // Strategy 3: Find by fuzzy title match (case-insensitive)
        if (!artwork && item.title) {
          artwork = await Artwork.findOne({
            title: new RegExp(`^${item.title}$`, 'i'),
            status: "published"
          }).populate("artistId", "name email avatarUrl");
        }

        // Strategy 4: Find by partial title match (last resort)
        if (!artwork && item.title) {
          const titleWords = item.title.split(/\s+/).filter(w => w.length > 3);
          if (titleWords.length > 0) {
            const titleRegex = new RegExp(titleWords.join('|'), 'i');
            artwork = await Artwork.findOne({
              title: titleRegex,
              status: "published"
            }).populate("artistId", "name email avatarUrl");
          }
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
              tags: artwork.tags,
              media: artwork.media,
              likeCount: artwork.likeCount,
              artistId: artwork.artistId,
              createdAt: artwork.createdAt
            }
          });
        } else {
          stats.missing_items++;
          const warningMsg = `Artwork not found: ${item.title || item.mongo_id || 'unknown'}`;
          console.warn(`⚠️ ${warningMsg}`);
          warnings.push(warningMsg);
        }
      } catch (error) {
        stats.missing_items++;
        console.error(`Error enriching item ${item.title}:`, error);
        warnings.push(`Error processing: ${item.title || 'unknown'} - ${error.message}`);
      }
    }

    // Include bundles with at least one valid item
    if (enrichedItems.length > 0) {
      const totalPrice = enrichedItems.reduce(
        (sum, item) => sum + (item.price || 0),
        0
      );

      enriched.push({
        ...bundle,
        items: enrichedItems,
        total_price: totalPrice,
        item_count: enrichedItems.length
      });
      
      stats.bundles_created++;
    } else {
      warnings.push(`Bundle "${bundle.bundle_name}" excluded - no valid items found`);
    }
  }

  // Log summary
  console.log('📊 Enrichment Summary:');
  console.log(`   Total items processed: ${stats.total_items}`);
  console.log(`   ✅ Found: ${stats.found_items}`);
  console.log(`   ❌ Missing: ${stats.missing_items}`);
  console.log(`   📦 Bundles created: ${stats.bundles_created}`);

  return {
    bundles: enriched,
    stats,
    warnings: warnings.length > 0 ? warnings : undefined
  };
}