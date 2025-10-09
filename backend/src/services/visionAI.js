// backend/src/services/visionAI.js
const axios = require("axios");
const FormData = require("form-data");

const AI_BASE = process.env.AI_SERVICES_URL || "http://localhost:5001";
const AI_API_KEY = process.env.AI_SERVICE_KEY || "";

/**
 * Fetch raw bytes from an accessible URL (Cloudinary secure_url)
 * Returns Buffer
 */
async function _fetchBytesFromUrl(url) {
  const resp = await axios.get(url, {
    responseType: "arraybuffer",
    timeout: 20000, // 20s timeout for fetch
  });
  return Buffer.from(resp.data);
}

/**
 * Optionally apply a simple Cloudinary resize transform to reduce payload.
 * If you have a Cloudinary URL like:
 *   https://res.cloudinary.com/<cloud_name>/image/upload/v1234/my.jpg
 * you can insert transformations after /upload/ e.g. /upload/w_800,h_800,c_limit/
 *
 * - transform: string like "w_800,h_800,c_limit"
 */
function cloudinaryTransform(url, transform) {
  if (!transform || !url) return url;
  // naive insertion: replace "/upload/" with "/upload/<transform>/"
  return url.replace("/upload/", `/upload/${transform}/`);
}

/**
 * postImageToAI
 * Accepts a `file` object:
 *  - multer memory: { buffer, originalname, mimetype }
 *  - cloudinary result (multer-storage-cloudinary): { secure_url, originalname, mimetype, path, url }
 */
async function postImageToAI(endpoint, file, options = {}) {
  // options: { cloudinaryTransform: "w_512,h_512,c_limit" }
  let buffer;
  let filename = file?.originalname || `upload-${Date.now()}.jpg`;
  let contentType = file?.mimetype || "image/jpeg";

  if (file?.buffer) {
    buffer = file.buffer;
  } else {
    // try common Cloudinary keys
    const url = file?.secure_url || file?.url || file?.path || file?.public_url;
    if (!url) throw new Error("No file buffer and no accessible file URL in request");

    // optionally shrink using Cloudinary transformation to reduce bytes
    const fetchUrl = options.cloudinaryTransform ? cloudinaryTransform(url, options.cloudinaryTransform) : url;
    buffer = await _fetchBytesFromUrl(fetchUrl);

    // derive filename from URL if not present
    if (!file.originalname) {
      const parts = fetchUrl.split("/");
      filename = parts[parts.length - 1].split("?")[0];
    }
  }

  // Build form-data
  const form = new FormData();
  // Microservice expects field named `image`
  form.append("image", buffer, { filename, contentType });

  const headers = {
    ...form.getHeaders(),
    ...(AI_API_KEY ? { "x-api-key": AI_API_KEY } : {}),
  };

  const url = `${AI_BASE}${endpoint}`;
  try {
    const resp = await axios.post(url, form, {
      headers,
      timeout: 30000, // 30s
    });
    return resp.data;
  } catch (err) {
    // Wrap error to include remote response if present
    const remote = err?.response?.data || err?.response?.statusText || err.message;
    throw new Error(`AI service request failed: ${JSON.stringify(remote)}`);
  }
}

// Exports: wrappers for each AI endpoint (match microservice routes)
module.exports = {
  generateStory: (file, opts) => postImageToAI("/vision/generate_story", file, opts),
  similarCrafts: (file, opts) => postImageToAI("/vision/similar_crafts", file, opts),
  priceSuggestion: (file, opts) => postImageToAI("/vision/price_suggestion", file, opts),
  complementaryProducts: (file, opts) => postImageToAI("/vision/complementary_products", file, opts),
  purchaseAnalysis: (file, opts) => postImageToAI("/vision/purchase_analysis", file, opts),
  fraudDetection: (file, opts) => postImageToAI("/vision/fraud_detection", file, opts),
  orderFulfillment: (file, opts) => postImageToAI("/vision/order_fulfillment_analysis", file, opts),
  qualityPredictions: (file, opts) => postImageToAI("/vision/quality_predictions", file, opts),
};
