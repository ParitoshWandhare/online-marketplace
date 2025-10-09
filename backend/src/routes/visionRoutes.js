// backend/src/routes/visionRoutes.js
const express = require("express");
const router = express.Router();
const upload = require("../middlewares/upload");
const visionController = require("../controllers/visionController");

// POST /api/vision/generate-story
router.post("/generate-story", upload.single("image"), visionController.generateStory);

// POST /api/vision/similar-crafts
router.post("/similar-crafts", upload.single("image"), visionController.similarCrafts);

// POST /api/vision/price-suggestion
router.post("/price-suggestion", upload.single("image"), visionController.priceSuggestion);

// POST /api/vision/complementary_products
router.post("/complementary-products", upload.single("image"), visionController.complementaryProducts);

// POST /api/vision/purchase_analysis
router.post("/purchase-analysis", upload.single("image"), visionController.purchaseAnalysis);

// POST /api/vision/fraud_detection
router.post("/fraud-detection", upload.single("image"), visionController.fraudDetection);

// POST /api/vision/order_fulfillment_analysis
router.post("/order_fulfillment_analysis", upload.single("image"), visionController.orderFulfillment);

// POST /api/vision/quality_predictions
router.post("/quality-predictions", upload.single("image"), visionController.qualityPredictions);

module.exports = router;
