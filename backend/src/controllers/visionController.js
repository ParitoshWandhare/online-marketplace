// backend/src/controllers/visionController.js
const visionAI = require("../services/visionAI");

const DEFAULT_TRANSFORM = "w_800,h_800,c_limit";

exports.generateStory = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.generateStory(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("generateStory error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err });
  }
};

exports.similarCrafts = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.similarCrafts(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("similarCrafts error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

exports.priceSuggestion = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.priceSuggestion(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("priceSuggestion error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

exports.complementaryProducts = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.complementaryProducts(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("complementaryProducts error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

exports.purchaseAnalysis = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.purchaseAnalysis(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("purchaseAnalysis error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

exports.fraudDetection = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.fraudDetection(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("fraudDetection error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

exports.orderFulfillment = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.orderFulfillment(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("orderFulfillment error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

exports.qualityPredictions = async (req, res) => {
  try {
    if (!req.file) return res.status(400).json({ error: "No image file provided" });
    const result = await visionAI.qualityPredictions(req.file, { cloudinaryTransform: DEFAULT_TRANSFORM });
    return res.json(result);
  } catch (err) {
    console.error("qualityPredictions error:", err?.response?.data || err.message || err);
    return res.status(502).json({ error: "AI service error", details: err?.message || err  });
  }
};

