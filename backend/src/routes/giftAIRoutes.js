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
 * Body: multipart/form-data with 'image' file
 */
router.post(
  "/generate-bundle",
  upload.single("image"),
  giftAIController.generateGiftBundle
);

/**
 * Search similar gifts by text query
 * GET /api/v1/gift-ai/search?query=birthday+gift&limit=10
 */
router.get("/search", giftAIController.searchSimilarGifts);

// ========================================================================
// VISION AI ENDPOINTS
// ========================================================================

/**
 * Analyze craft type from image
 * POST /api/v1/gift-ai/analyze-craft
 */
router.post(
  "/analyze-craft",
  upload.single("image"),
  giftAIController.analyzeCraft
);

/**
 * Analyze quality from image
 * POST /api/v1/gift-ai/analyze-quality
 */
router.post(
  "/analyze-quality",
  upload.single("image"),
  giftAIController.analyzeQuality
);

/**
 * Estimate price from image
 * POST /api/v1/gift-ai/estimate-price
 */
router.post(
  "/estimate-price",
  upload.single("image"),
  giftAIController.estimatePrice
);

/**
 * Detect fraud indicators
 * POST /api/v1/gift-ai/detect-fraud
 */
router.post(
  "/detect-fraud",
  upload.single("image"),
  giftAIController.detectFraud
);

/**
 * Detect suitable occasion
 * POST /api/v1/gift-ai/detect-occasion
 */
router.post(
  "/detect-occasion",
  upload.single("image"),
  giftAIController.detectOccasion
);

// ========================================================================
// ADMIN ENDPOINTS (Requires authentication)
// ========================================================================

/**
 * Refresh vector store (sync MongoDB → Qdrant)
 * POST /api/v1/gift-ai/refresh-vector-store
 * Requires: Authentication
 */
router.post(
  "/refresh-vector-store",
  isAuthenticated,
  giftAIController.refreshVectorStore
);

/**
 * Get vector store information
 * GET /api/v1/gift-ai/vector-store-info
 * Requires: Authentication
 */
router.get(
  "/vector-store-info",
  isAuthenticated,
  giftAIController.getVectorStoreInfo
);

/**
 * Index a specific artwork
 * POST /api/v1/gift-ai/index-artwork/:artworkId
 * Requires: Authentication
 */
router.post(
  "/index-artwork/:artworkId",
  isAuthenticated,
  giftAIController.indexArtwork
);

module.exports = router;