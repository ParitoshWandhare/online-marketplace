// backend/src/routes/giftAIRoutes.js
const express = require("express");
const multer = require("multer");
const giftAIController = require("../controllers/giftAIController");
const isAuthenticated = require("../middlewares/authMiddleware");

const router = express.Router();

// Configure multer for memory storage (we'll pass buffer to AI service)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 5 * 1024 * 1024, // 5MB limit
  },
  fileFilter: (req, file, cb) => {
    // Accept images only
    if (file.mimetype.startsWith("image/")) {
      cb(null, true);
    } else {
      cb(new Error("Only image files are allowed"), false);
    }
  },
});

// ========================================================================
// PUBLIC ENDPOINTS (No authentication required for demo/testing)
// ========================================================================

/**
 * Health check for AI services
 * GET /api/v1/gift-ai/health
 */
router.get("/health", giftAIController.healthCheck);

/**
 * Generate gift bundle from image
 * POST /api/v1/gift-ai/generate-bundle
 * POST /api/v1/gift-ai/generate_gift_bundle (alias for compatibility)
 * Body: multipart/form-data with 'image' file
 */
router.post(
  "/generate-bundle",
  upload.single("image"),
  giftAIController.generateGiftBundle
);

// Add alias route for underscore version
router.post(
  "/generate_gift_bundle",
  upload.single("image"),
  giftAIController.generateGiftBundle
);

/**
 * Search similar gifts by text query
 * GET /api/v1/gift-ai/search?query=birthday+gift&limit=10
 * POST /api/v1/gift-ai/search_similar_gifts (alias for compatibility)
 */
router.get("/search", giftAIController.searchSimilarGifts);

// Add alias route for underscore version
router.post("/search_similar_gifts", giftAIController.searchSimilarGifts);

// ========================================================================
// VISION AI ENDPOINTS
// ========================================================================

/**
 * Analyze craft type from image
 * POST /api/v1/gift-ai/analyze-craft
 * POST /api/v1/gift-ai/analyze_craft (alias for compatibility)
 */
router.post(
  "/analyze-craft",
  upload.single("image"),
  giftAIController.analyzeCraft
);

// Add alias route for underscore version
router.post(
  "/analyze_craft",
  upload.single("image"),
  giftAIController.analyzeCraft
);

/**
 * Analyze quality from image
 * POST /api/v1/gift-ai/analyze-quality
 * POST /api/v1/gift-ai/analyze_quality (alias for compatibility)
 */
router.post(
  "/analyze-quality",
  upload.single("image"),
  giftAIController.analyzeQuality
);

// Add alias route for underscore version
router.post(
  "/analyze_quality",
  upload.single("image"),
  giftAIController.analyzeQuality
);

/**
 * Estimate price from image
 * POST /api/v1/gift-ai/estimate-price
 * POST /api/v1/gift-ai/estimate_price (alias for compatibility)
 */
router.post(
  "/estimate-price",
  upload.single("image"),
  giftAIController.estimatePrice
);

// Add alias route for underscore version
router.post(
  "/estimate_price",
  upload.single("image"),
  giftAIController.estimatePrice
);

/**
 * Detect fraud indicators
 * POST /api/v1/gift-ai/detect-fraud
 * POST /api/v1/gift-ai/detect_fraud (alias for compatibility)
 */
router.post(
  "/detect-fraud",
  upload.single("image"),
  giftAIController.detectFraud
);

// Add alias route for underscore version
router.post(
  "/detect_fraud",
  upload.single("image"),
  giftAIController.detectFraud
);

/**
 * Detect suitable occasion
 * POST /api/v1/gift-ai/detect-occasion
 * POST /api/v1/gift-ai/detect_occasion (alias for compatibility)
 */
router.post(
  "/detect-occasion",
  upload.single("image"),
  giftAIController.detectOccasion
);

// Add alias route for underscore version
router.post(
  "/detect_occasion",
  upload.single("image"),
  giftAIController.detectOccasion
);

// ========================================================================
// ADMIN ENDPOINTS (Requires authentication)
// ========================================================================

/**
 * Refresh vector store (sync MongoDB → Qdrant)
 * POST /api/v1/gift-ai/refresh-vector-store
 * POST /api/v1/gift-ai/refresh_vector_store (alias for compatibility)
 * Requires: Authentication
 */
router.post(
  "/refresh-vector-store",
  isAuthenticated,
  giftAIController.refreshVectorStore
);

// Add alias route for underscore version
router.post(
  "/refresh_vector_store",
  isAuthenticated,
  giftAIController.refreshVectorStore
);

/**
 * Get vector store information
 * GET /api/v1/gift-ai/vector-store-info
 * GET /api/v1/gift-ai/vector_store_info (alias for compatibility)
 * Requires: Authentication
 */
router.get(
  "/vector-store-info",
  isAuthenticated,
  giftAIController.getVectorStoreInfo
);

// Add alias route for underscore version
router.get(
  "/vector_store_info",
  isAuthenticated,
  giftAIController.getVectorStoreInfo
);

/**
 * Index a specific artwork
 * POST /api/v1/gift-ai/index-artwork/:artworkId
 * POST /api/v1/gift-ai/index_artwork/:artworkId (alias for compatibility)
 * Requires: Authentication
 */
router.post(
  "/index-artwork/:artworkId",
  isAuthenticated,
  giftAIController.indexArtwork
);

// Add alias route for underscore version
router.post(
  "/index_artwork/:artworkId",
  isAuthenticated,
  giftAIController.indexArtwork
);

module.exports = router;