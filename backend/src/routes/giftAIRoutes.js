// backend/src/routes/giftAIRoutes.js
/**
 * Gift AI Routes - Updated with Async Processing Support
 * FIXES:
 * - Added async endpoints for operations that may exceed Azure's 230s timeout
 * - Status checking endpoints for long-running operations
 * - Better error handling
 */

const express = require("express");
const multer = require("multer");
const giftAIController = require("../controllers/giftAIController");
const isAuthenticated = require("../middlewares/authMiddleware");

const router = express.Router();

// Configure multer for memory storage
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB limit
  },
  fileFilter: (req, file, cb) => {
    if (file.mimetype.startsWith("image/")) {
      cb(null, true);
    } else {
      cb(new Error("Only image files are allowed"), false);
    }
  },
});

// ========================================================================
// IN-MEMORY STORAGE FOR ASYNC OPERATIONS
// ========================================================================
const pendingOperations = new Map();

// Cleanup old operations (1 hour retention)
setInterval(() => {
  const oneHourAgo = Date.now() - 3600000;
  for (const [operationId, operation] of pendingOperations.entries()) {
    if (operation.createdAt < oneHourAgo) {
      pendingOperations.delete(operationId);
      console.log(`🧹 Cleaned up operation: ${operationId}`);
    }
  }
}, 300000); // Run every 5 minutes

// ========================================================================
// PUBLIC ENDPOINTS
// ========================================================================

/**
 * Health check for AI services
 * GET /api/v1/gift-ai/health
 */
router.get("/health", giftAIController.healthCheck);

/**
 * Generate gift bundle from image (SYNCHRONOUS)
 * POST /api/v1/gift-ai/generate-bundle
 * Timeout: 180 seconds (3 minutes)
 */
router.post(
  "/generate-bundle",
  upload.single("image"),
  giftAIController.generateGiftBundle
);

// Alias for compatibility
router.post(
  "/generate_gift_bundle",
  upload.single("image"),
  giftAIController.generateGiftBundle
);

/**
 * Generate gift bundle from image (ASYNCHRONOUS)
 * POST /api/v1/gift-ai/generate-bundle-async
 * Returns immediately with operation ID
 */
router.post(
  "/generate-bundle-async",
  upload.single("image"),
  async (req, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({
          success: false,
          message: "No image file provided",
        });
      }

      // Generate operation ID
      const operationId = `bundle_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      // Store initial status
      pendingOperations.set(operationId, {
        status: "processing",
        createdAt: Date.now(),
        message: "Processing your gift bundle request..."
      });

      console.log(`🎁 Starting async bundle generation: ${operationId}`);

      // Return immediately
      res.json({
        success: true,
        operationId,
        status: "processing",
        statusUrl: `/api/v1/gift-ai/status/${operationId}`,
        message: "Your request is being processed. Check the status URL for results."
      });

      // Process in background
      (async () => {
        try {
          // Update status
          pendingOperations.set(operationId, {
            status: "processing",
            createdAt: Date.now(),
            message: "Analyzing image with AI..."
          });

          // Call the actual controller logic
          const giftAIService = require("../services/giftAIService");
          const result = await giftAIService.generateGiftBundle(
            req.file.buffer,
            req.file.originalname
          );

          if (!result.success) {
            throw new Error(result.error || "Bundle generation failed");
          }

          // Enrich bundles (same logic as controller)
          const Artwork = require("../models/Artwork");
          const enrichedBundles = await enrichBundlesWithArtworkData(result.data.bundles);

          // Store success result
          pendingOperations.set(operationId, {
            status: "completed",
            createdAt: Date.now(),
            result: {
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
            }
          });

          console.log(`✅ Async bundle generation completed: ${operationId}`);

        } catch (error) {
          console.error(`❌ Async bundle generation failed: ${operationId}`, error);
          
          pendingOperations.set(operationId, {
            status: "failed",
            createdAt: Date.now(),
            error: error.message || "Unknown error"
          });
        }
      })();

    } catch (error) {
      console.error("Error starting async operation:", error);
      res.status(500).json({
        success: false,
        message: "Failed to start async operation",
        error: error.message,
      });
    }
  }
);

/**
 * Check status of async operation
 * GET /api/v1/gift-ai/status/:operationId
 */
router.get("/status/:operationId", (req, res) => {
  const { operationId } = req.params;
  
  const operation = pendingOperations.get(operationId);
  
  if (!operation) {
    return res.status(404).json({
      success: false,
      message: "Operation not found or expired",
      operationId
    });
  }

  // Return current status
  if (operation.status === "completed") {
    return res.json({
      success: true,
      status: "completed",
      operationId,
      ...operation.result
    });
  } else if (operation.status === "failed") {
    return res.status(500).json({
      success: false,
      status: "failed",
      operationId,
      error: operation.error
    });
  } else {
    return res.json({
      success: true,
      status: "processing",
      operationId,
      message: operation.message || "Processing..."
    });
  }
});

/**
 * Search similar gifts by text query
 * GET /api/v1/gift-ai/search?query=...&limit=10
 * POST /api/v1/gift-ai/search_similar_gifts (for compatibility)
 */
router.get("/search", giftAIController.searchSimilarGifts);

router.post("/search_similar_gifts", giftAIController.searchSimilarGifts);

// ========================================================================
// VISION AI ENDPOINTS
// ========================================================================

router.post(
  "/analyze-craft",
  upload.single("image"),
  giftAIController.analyzeCraft
);

router.post(
  "/analyze_craft",
  upload.single("image"),
  giftAIController.analyzeCraft
);

router.post(
  "/analyze-quality",
  upload.single("image"),
  giftAIController.analyzeQuality
);

router.post(
  "/analyze_quality",
  upload.single("image"),
  giftAIController.analyzeQuality
);

router.post(
  "/estimate-price",
  upload.single("image"),
  giftAIController.estimatePrice
);

router.post(
  "/estimate_price",
  upload.single("image"),
  giftAIController.estimatePrice
);

router.post(
  "/detect-fraud",
  upload.single("image"),
  giftAIController.detectFraud
);

router.post(
  "/detect_fraud",
  upload.single("image"),
  giftAIController.detectFraud
);

router.post(
  "/detect-occasion",
  upload.single("image"),
  giftAIController.detectOccasion
);

router.post(
  "/detect_occasion",
  upload.single("image"),
  giftAIController.detectOccasion
);

// ========================================================================
// ADMIN ENDPOINTS (Requires authentication)
// ========================================================================

router.post(
  "/refresh-vector-store",
  isAuthenticated,
  giftAIController.refreshVectorStore
);

router.post(
  "/refresh_vector_store",
  isAuthenticated,
  giftAIController.refreshVectorStore
);

router.get(
  "/vector-store-info",
  isAuthenticated,
  giftAIController.getVectorStoreInfo
);

router.get(
  "/vector_store_info",
  isAuthenticated,
  giftAIController.getVectorStoreInfo
);

router.post(
  "/index-artwork/:artworkId",
  isAuthenticated,
  giftAIController.indexArtwork
);

router.post(
  "/index_artwork/:artworkId",
  isAuthenticated,
  giftAIController.indexArtwork
);

// ========================================================================
// HELPER FUNCTIONS
// ========================================================================

/**
 * Enrich AI bundles with full artwork data from MongoDB
 */
async function enrichBundlesWithArtworkData(bundles) {
  const Artwork = require("../models/Artwork");
  
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

module.exports = router;