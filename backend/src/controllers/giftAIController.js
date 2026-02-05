// // backend/src/controllers/giftAIController.js
// const giftAIService = require("../services/giftAIService");
// const Artwork = require("../models/Artwork");

// // ========================================================================
// // GIFT BUNDLE GENERATION
// // ========================================================================

// /**
//  * Generate gift bundle from uploaded image
//  * POST /api/v1/gift-ai/generate-bundle
//  */
// exports.generateGiftBundle = async (req, res) => {
//   try {
//     if (!req.file) {
//       return res.status(400).json({
//         success: false,
//         message: "No image file provided",
//       });
//     }

//     console.log("📸 Processing gift bundle request for:", req.file.originalname);

//     // Call AI service
//     const result = await giftAIService.generateGiftBundle(
//       req.file.buffer,
//       req.file.originalname
//     );

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Gift bundle generation failed",
//         error: result.error,
//       });
//     }

//     // Enrich bundles with actual artwork data from MongoDB
//     const enrichmentResult = await enrichBundlesWithArtworkData(
//       result.data.bundles
//     );

//     res.json({
//       success: true,
//       message: "Gift bundle generated successfully",
//       bundle_id: result.data.bundle_id,
//       vision: result.data.vision,
//       intent: result.data.intent,
//       bundles: enrichmentResult.bundles,
//       metadata: {
//         ...result.data.metadata,
//         enrichment_stats: enrichmentResult.stats
//       },
//       warnings: enrichmentResult.warnings
//     });
//   } catch (error) {
//     console.error("Error in generateGiftBundle:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// // ========================================================================
// // TEXT SEARCH FOR GIFTS
// // ========================================================================

// /**
//  * Search similar gifts by text query
//  * GET /api/v1/gift-ai/search?query=...&limit=10
//  * POST /api/v1/gift-ai/search_similar_gifts (for compatibility)
//  */
// exports.searchSimilarGifts = async (req, res) => {
//   try {
//     // Handle both GET and POST requests
//     const { query, limit } = req.method === 'GET' ? req.query : req.body;

//     if (!query || query.trim().length === 0) {
//       return res.status(400).json({
//         success: false,
//         message: "Search query is required",
//       });
//     }

//     const searchLimit = parseInt(limit) || 10;

//     console.log(`🔍 Searching gifts for: "${query}"`);

//     const result = await giftAIService.searchSimilarGifts(query, searchLimit);

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Gift search failed",
//         error: result.error,
//       });
//     }

//     // Enrich with MongoDB data
//     const enrichmentResult = await enrichBundlesWithArtworkData(
//       result.data.bundles
//     );

//     res.json({
//       success: true,
//       query: query,
//       count: enrichmentResult.bundles.length,
//       bundles: enrichmentResult.bundles,
//       metadata: {
//         ...result.data.metadata,
//         enrichment_stats: enrichmentResult.stats
//       },
//       warnings: enrichmentResult.warnings
//     });
//   } catch (error) {
//     console.error("Error in searchSimilarGifts:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// // ========================================================================
// // VISION AI ENDPOINTS
// // ========================================================================

// /**
//  * Analyze craft type from image
//  * POST /api/v1/gift-ai/analyze-craft
//  */
// exports.analyzeCraft = async (req, res) => {
//   try {
//     if (!req.file) {
//       return res.status(400).json({
//         success: false,
//         message: "No image file provided",
//       });
//     }

//     const result = await giftAIService.analyzeCraft(
//       req.file.buffer,
//       req.file.originalname
//     );

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Craft analysis failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in analyzeCraft:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Analyze quality from image
//  * POST /api/v1/gift-ai/analyze-quality
//  */
// exports.analyzeQuality = async (req, res) => {
//   try {
//     if (!req.file) {
//       return res.status(400).json({
//         success: false,
//         message: "No image file provided",
//       });
//     }

//     const result = await giftAIService.analyzeQuality(
//       req.file.buffer,
//       req.file.originalname
//     );

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Quality analysis failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in analyzeQuality:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Estimate price from image
//  * POST /api/v1/gift-ai/estimate-price
//  */
// exports.estimatePrice = async (req, res) => {
//   try {
//     if (!req.file) {
//       return res.status(400).json({
//         success: false,
//         message: "No image file provided",
//       });
//     }

//     const result = await giftAIService.estimatePrice(
//       req.file.buffer,
//       req.file.originalname
//     );

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Price estimation failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in estimatePrice:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Detect fraud indicators
//  * POST /api/v1/gift-ai/detect-fraud
//  */
// exports.detectFraud = async (req, res) => {
//   try {
//     if (!req.file) {
//       return res.status(400).json({
//         success: false,
//         message: "No image file provided",
//       });
//     }

//     const result = await giftAIService.detectFraud(
//       req.file.buffer,
//       req.file.originalname
//     );

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Fraud detection failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in detectFraud:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Detect occasion from image
//  * POST /api/v1/gift-ai/detect-occasion
//  */
// exports.detectOccasion = async (req, res) => {
//   try {
//     if (!req.file) {
//       return res.status(400).json({
//         success: false,
//         message: "No image file provided",
//       });
//     }

//     const result = await giftAIService.detectOccasion(
//       req.file.buffer,
//       req.file.originalname
//     );

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Occasion detection failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in detectOccasion:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// // ========================================================================
// // ADMIN ENDPOINTS
// // ========================================================================

// /**
//  * Refresh vector store (Admin only)
//  * POST /api/v1/gift-ai/refresh-vector-store
//  */
// exports.refreshVectorStore = async (req, res) => {
//   try {
//     console.log("🔄 Starting vector store refresh...");

//     const result = await giftAIService.refreshVectorStore();

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Vector store refresh failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       message: "Vector store refreshed successfully",
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in refreshVectorStore:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Get vector store info
//  * GET /api/v1/gift-ai/vector-store-info
//  */
// exports.getVectorStoreInfo = async (req, res) => {
//   try {
//     const result = await giftAIService.getVectorStoreInfo();

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Failed to fetch vector store info",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in getVectorStoreInfo:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Index artwork when created/updated
//  * POST /api/v1/gift-ai/index-artwork/:artworkId
//  */
// exports.indexArtwork = async (req, res) => {
//   try {
//     const { artworkId } = req.params;

//     const artwork = await Artwork.findById(artworkId);
//     if (!artwork) {
//       return res.status(404).json({
//         success: false,
//         message: "Artwork not found",
//       });
//     }

//     const result = await giftAIService.indexArtwork(artwork);

//     if (!result.success) {
//       return res.status(500).json({
//         success: false,
//         message: "Artwork indexing failed",
//         error: result.error,
//       });
//     }

//     res.json({
//       success: true,
//       message: "Artwork indexed successfully",
//       data: result.data,
//     });
//   } catch (error) {
//     console.error("Error in indexArtwork:", error);
//     res.status(500).json({
//       success: false,
//       message: "Internal server error",
//       error: error.message,
//     });
//   }
// };

// /**
//  * Health check for AI services
//  * GET /api/v1/gift-ai/health
//  */
// exports.healthCheck = async (req, res) => {
//   try {
//     const giftServiceHealthy = await giftAIService.isGiftServiceHealthy();
//     const visionServiceHealthy = await giftAIService.isVisionServiceHealthy();

//     res.json({
//       success: true,
//       services: {
//         gift_ai: {
//           status: giftServiceHealthy ? "healthy" : "unhealthy",
//           url: process.env.GIFT_AI_SERVICE_URL || "Not configured",
//         },
//         vision_ai: {
//           status: visionServiceHealthy ? "healthy" : "unhealthy",
//           url: process.env.VISION_AI_SERVICE_URL || process.env.GIFT_AI_SERVICE_URL || "Not configured",
//         },
//       },
//       all_healthy: giftServiceHealthy && visionServiceHealthy,
//     });
//   } catch (error) {
//     console.error("Error in healthCheck:", error);
//     res.status(500).json({
//       success: false,
//       message: "Health check failed",
//       error: error.message,
//     });
//   }
// };

// // ========================================================================
// // HELPER FUNCTIONS
// // ========================================================================

// /**
//  * Enrich AI bundles with full artwork data from MongoDB
//  * Now includes detailed stats and warnings
//  */
// async function enrichBundlesWithArtworkData(bundles) {
//   if (!bundles || bundles.length === 0) {
//     return {
//       bundles: [],
//       stats: { total: 0, found: 0, missing: 0 },
//       warnings: []
//     };
//   }

//   const enriched = [];
//   const warnings = [];
//   const stats = {
//     total_items: 0,
//     found_items: 0,
//     missing_items: 0,
//     bundles_created: 0
//   };

//   for (const bundle of bundles) {
//     const enrichedItems = [];

//     for (const item of bundle.items || []) {
//       stats.total_items++;
      
//       try {
//         let artwork = null;

//         // Strategy 1: Find by mongo_id
//         if (item.mongo_id) {
//           try {
//             artwork = await Artwork.findById(item.mongo_id)
//               .populate("artistId", "name email avatarUrl");
//           } catch (err) {
//             console.warn(`⚠️ Invalid mongo_id: ${item.mongo_id}`);
//           }
//         }

//         // Strategy 2: Find by exact title match
//         if (!artwork && item.title) {
//           artwork = await Artwork.findOne({
//             title: item.title,
//             status: "published"
//           }).populate("artistId", "name email avatarUrl");
//         }

//         // Strategy 3: Find by fuzzy title match (case-insensitive)
//         if (!artwork && item.title) {
//           artwork = await Artwork.findOne({
//             title: new RegExp(`^${item.title}$`, 'i'),
//             status: "published"
//           }).populate("artistId", "name email avatarUrl");
//         }

//         // Strategy 4: Find by partial title match (last resort)
//         if (!artwork && item.title) {
//           const titleWords = item.title.split(/\s+/).filter(w => w.length > 3);
//           if (titleWords.length > 0) {
//             const titleRegex = new RegExp(titleWords.join('|'), 'i');
//             artwork = await Artwork.findOne({
//               title: titleRegex,
//               status: "published"
//             }).populate("artistId", "name email avatarUrl");
//           }
//         }

//         if (artwork) {
//           stats.found_items++;
//           enrichedItems.push({
//             mongo_id: artwork._id.toString(),
//             title: artwork.title,
//             reason: item.reason || "Recommended for you",
//             price: artwork.price,
//             currency: artwork.currency || "INR",
//             artwork: {
//               _id: artwork._id,
//               title: artwork.title,
//               description: artwork.description,
//               price: artwork.price,
//               currency: artwork.currency,
//               quantity: artwork.quantity,
//               status: artwork.status,
//               tags: artwork.tags,
//               media: artwork.media,
//               likeCount: artwork.likeCount,
//               artistId: artwork.artistId,
//               createdAt: artwork.createdAt
//             }
//           });
//         } else {
//           stats.missing_items++;
//           const warningMsg = `Artwork not found: ${item.title || item.mongo_id || 'unknown'}`;
//           console.warn(`⚠️ ${warningMsg}`);
//           warnings.push(warningMsg);
//         }
//       } catch (error) {
//         stats.missing_items++;
//         console.error(`Error enriching item ${item.title}:`, error);
//         warnings.push(`Error processing: ${item.title || 'unknown'} - ${error.message}`);
//       }
//     }

//     // Include bundles with at least one valid item
//     if (enrichedItems.length > 0) {
//       const totalPrice = enrichedItems.reduce(
//         (sum, item) => sum + (item.price || 0),
//         0
//       );

//       enriched.push({
//         ...bundle,
//         items: enrichedItems,
//         total_price: totalPrice,
//         item_count: enrichedItems.length
//       });
      
//       stats.bundles_created++;
//     } else {
//       warnings.push(`Bundle "${bundle.bundle_name}" excluded - no valid items found`);
//     }
//   }

//   // Log summary
//   console.log('📊 Enrichment Summary:');
//   console.log(`   Total items processed: ${stats.total_items}`);
//   console.log(`   ✅ Found: ${stats.found_items}`);
//   console.log(`   ❌ Missing: ${stats.missing_items}`);
//   console.log(`   📦 Bundles created: ${stats.bundles_created}`);

//   return {
//     bundles: enriched,
//     stats,
//     warnings: warnings.length > 0 ? warnings : undefined
//   };
// }


// backend/src/controllers/giftAIController.js
const giftAIService = require("../services/giftAIService");
const Artwork = require("../models/Artwork");

// ========================================================================
// HELPER FUNCTIONS (Defined at top for hoisting)
// ========================================================================

/**
 * Centralized error handler for all controller functions
 * @param {Error} error - The error object
 * @param {Object} res - Express response object
 * @param {string} defaultMessage - Default error message
 */
function handleControllerError(error, res, defaultMessage = "Internal server error") {
  console.error(`❌ Controller Error:`, {
    message: error.message,
    stack: process.env.NODE_ENV === 'development' ? error.stack : undefined,
    details: error.response?.data || error.details
  });
  
  const statusCode = error.response?.status || error.statusCode || 500;
  const errorMessage = error.response?.data?.detail || 
                       error.response?.data?.message || 
                       error.message || 
                       defaultMessage;
  
  return res.status(statusCode).json({
    success: false,
    message: errorMessage,
    error: process.env.NODE_ENV === 'development' ? error.message : undefined,
    timestamp: new Date().toISOString()
  });
}

/**
 * Enrich AI bundles with full artwork data from MongoDB
 * Includes detailed stats, warnings, and multiple search strategies
 * 
 * @param {Array} bundles - Array of bundle objects from AI service
 * @returns {Object} - Enriched bundles with stats and warnings
 */
async function enrichBundlesWithArtworkData(bundles) {
  // Handle empty or invalid input
  if (!bundles || !Array.isArray(bundles) || bundles.length === 0) {
    console.log('⚠️ No bundles to enrich');
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

  console.log(`📦 Enriching ${bundles.length} bundles...`);

  for (const bundle of bundles) {
    const enrichedItems = [];
    const bundleName = bundle.bundle_name || bundle.name || 'Unnamed Bundle';

    // Validate bundle has items
    if (!bundle.items || !Array.isArray(bundle.items) || bundle.items.length === 0) {
      warnings.push(`Bundle "${bundleName}" has no items - skipping`);
      continue;
    }

    for (const item of bundle.items) {
      stats.total_items++;
      
      try {
        let artwork = null;

        // Strategy 1: Find by mongo_id (most reliable)
        if (item.mongo_id) {
          try {
            artwork = await Artwork.findById(item.mongo_id)
              .populate("artistId", "name email avatarUrl");
            
            if (artwork) {
              console.log(`✅ Found by mongo_id: ${item.mongo_id}`);
            }
          } catch (err) {
            console.warn(`⚠️ Invalid mongo_id format: ${item.mongo_id} - ${err.message}`);
          }
        }

        // Strategy 2: Find by exact title match (published items only)
        if (!artwork && item.title) {
          artwork = await Artwork.findOne({
            title: item.title,
            status: "published"
          }).populate("artistId", "name email avatarUrl");
          
          if (artwork) {
            console.log(`✅ Found by exact title: "${item.title}"`);
          }
        }

        // Strategy 3: Find by case-insensitive title match
        if (!artwork && item.title) {
          artwork = await Artwork.findOne({
            title: new RegExp(`^${escapeRegex(item.title)}$`, 'i'),
            status: "published"
          }).populate("artistId", "name email avatarUrl");
          
          if (artwork) {
            console.log(`✅ Found by case-insensitive title: "${item.title}"`);
          }
        }

        // Strategy 4: Find by partial title match (fuzzy search - last resort)
        if (!artwork && item.title) {
          const titleWords = item.title
            .split(/\s+/)
            .filter(word => word.length > 3) // Only meaningful words
            .map(escapeRegex);
          
          if (titleWords.length > 0) {
            const titleRegex = new RegExp(titleWords.join('|'), 'i');
            artwork = await Artwork.findOne({
              title: titleRegex,
              status: "published"
            }).populate("artistId", "name email avatarUrl");
            
            if (artwork) {
              console.log(`✅ Found by fuzzy match: "${item.title}" → "${artwork.title}"`);
            }
          }
        }

        // If artwork found, add to enriched items
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
          // Artwork not found - log and track
          stats.missing_items++;
          const identifier = item.title || item.mongo_id || 'unknown';
          const warningMsg = `Artwork not found: "${identifier}"`;
          console.warn(`⚠️ ${warningMsg}`);
          warnings.push(warningMsg);
        }
      } catch (error) {
        // Error during enrichment - log and track
        stats.missing_items++;
        const identifier = item.title || item.mongo_id || 'unknown';
        const errorMsg = `Error processing: "${identifier}" - ${error.message}`;
        console.error(`❌ ${errorMsg}`);
        warnings.push(errorMsg);
      }
    }

    // Only include bundles with at least one valid item
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
      console.log(`✅ Bundle "${bundleName}": ${enrichedItems.length}/${bundle.items.length} items enriched`);
    } else {
      const warningMsg = `Bundle "${bundleName}" excluded - no valid items found (0/${bundle.items.length})`;
      console.warn(`⚠️ ${warningMsg}`);
      warnings.push(warningMsg);
    }
  }

  // Log enrichment summary
  console.log('\n📊 Enrichment Summary:');
  console.log(`   Total items processed: ${stats.total_items}`);
  console.log(`   ✅ Found: ${stats.found_items}`);
  console.log(`   ❌ Missing: ${stats.missing_items}`);
  console.log(`   📦 Bundles created: ${stats.bundles_created}/${bundles.length}`);
  console.log(`   ⚠️  Warnings: ${warnings.length}\n`);

  return {
    bundles: enriched,
    stats,
    warnings: warnings.length > 0 ? warnings : undefined
  };
}

/**
 * Escape special regex characters in a string
 * @param {string} string - String to escape
 * @returns {string} - Escaped string
 */
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ========================================================================
// GIFT BUNDLE GENERATION
// ========================================================================

/**
 * Generate gift bundle from uploaded image
 * POST /api/v1/gift-ai/generate-bundle
 */
exports.generateGiftBundle = async (req, res) => {
  try {
    // Validate file upload
    if (!req.file) {
      return res.status(400).json({
        success: false,
        message: "No image file provided",
      });
    }

    // Validate file size (max 5MB)
    if (req.file.size > 5 * 1024 * 1024) {
      return res.status(400).json({
        success: false,
        message: "Image file too large. Maximum size is 5MB",
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
        details: result.details
      });
    }

    // Enrich bundles with actual artwork data from MongoDB
    const enrichmentResult = await enrichBundlesWithArtworkData(
      result.data.bundles
    );

    // Send successful response
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
    return handleControllerError(error, res, "Internal server error generating gift bundle");
  }
};

// ========================================================================
// TEXT SEARCH FOR GIFTS
// ========================================================================

/**
 * Search similar gifts by text query
 * GET /api/v1/gift-ai/search?query=...&limit=10
 * POST /api/v1/gift-ai/search_similar_gifts (for compatibility)
 */
exports.searchSimilarGifts = async (req, res) => {
  try {
    // Handle both GET and POST requests
    const { query, limit } = req.method === 'GET' ? req.query : req.body;

    // Validate query
    if (!query || query.trim().length === 0) {
      return res.status(400).json({
        success: false,
        message: "Search query is required",
      });
    }

    // Validate and parse limit
    const searchLimit = Math.min(parseInt(limit) || 10, 50); // Max 50 items

    console.log(`🔍 Searching gifts for: "${query}" (limit: ${searchLimit})`);

    // Call AI service
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

    // Send successful response
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
    return handleControllerError(error, res, "Internal server error searching gifts");
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
    return handleControllerError(error, res, "Internal server error analyzing craft");
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
    return handleControllerError(error, res, "Internal server error analyzing quality");
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
    return handleControllerError(error, res, "Internal server error estimating price");
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
    return handleControllerError(error, res, "Internal server error detecting fraud");
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
    return handleControllerError(error, res, "Internal server error detecting occasion");
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
    return handleControllerError(error, res, "Internal server error refreshing vector store");
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
    return handleControllerError(error, res, "Internal server error fetching vector store info");
  }
};

/**
 * Index artwork when created/updated
 * POST /api/v1/gift-ai/index-artwork/:artworkId
 */
exports.indexArtwork = async (req, res) => {
  try {
    const { artworkId } = req.params;

    // Validate artworkId
    if (!artworkId) {
      return res.status(400).json({
        success: false,
        message: "Artwork ID is required",
      });
    }

    // Find artwork
    const artwork = await Artwork.findById(artworkId);
    if (!artwork) {
      return res.status(404).json({
        success: false,
        message: "Artwork not found",
      });
    }

    // Index artwork
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
    return handleControllerError(error, res, "Internal server error indexing artwork");
  }
};

/**
 * Health check for AI services
 * GET /api/v1/gift-ai/health
 */
exports.healthCheck = async (req, res) => {
  try {
    // Check both services with timeout
    const healthCheckTimeout = 5000; // 5 seconds
    
    const [giftServiceHealthy, visionServiceHealthy] = await Promise.all([
      Promise.race([
        giftAIService.isGiftServiceHealthy(),
        new Promise(resolve => setTimeout(() => resolve(false), healthCheckTimeout))
      ]),
      Promise.race([
        giftAIService.isVisionServiceHealthy(),
        new Promise(resolve => setTimeout(() => resolve(false), healthCheckTimeout))
      ])
    ]);

    const allHealthy = giftServiceHealthy && visionServiceHealthy;

    res.status(allHealthy ? 200 : 503).json({
      success: true,
      services: {
        gift_ai: {
          status: giftServiceHealthy ? "healthy" : "unhealthy",
          url: process.env.GIFT_AI_SERVICE_URL || "Not configured",
        },
        vision_ai: {
          status: visionServiceHealthy ? "healthy" : "unhealthy",
          url: process.env.VISION_AI_SERVICE_URL || process.env.GIFT_AI_SERVICE_URL || "Not configured",
        },
      },
      all_healthy: allHealthy,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    return handleControllerError(error, res, "Health check failed");
  }
};