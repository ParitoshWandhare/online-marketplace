// // backend/src/services/visionAI.js
// const axios = require("axios");
// const FormData = require("form-data");

// // Use VISION_AI_SERVICE_URL instead of AI_SERVICES_URL
// const AI_BASE = process.env.AI_SERVICES_URL || process.env.VISION_AI_SERVICE_URL || "https://orchid-genai.azurewebsites.net/";
// const AI_API_KEY = process.env.AI_SERVICE_KEY || "";

// console.log(`🔧 Vision AI Service URL: ${AI_BASE}`);

// /**
//  * Fetch raw bytes from an accessible URL (Cloudinary secure_url)
//  * Returns Buffer
//  */
// async function _fetchBytesFromUrl(url) {
//   const resp = await axios.get(url, {
//     responseType: "arraybuffer",
//     timeout: 20000, // 20s timeout for fetch
//   });
//   return Buffer.from(resp.data);
// }

// /**
//  * Optionally apply a simple Cloudinary resize transform to reduce payload.
//  * If you have a Cloudinary URL like:
//  *   https://res.cloudinary.com/<cloud_name>/image/upload/v1234/my.jpg
//  * you can insert transformations after /upload/ e.g. /upload/w_800,h_800,c_limit/
//  *
//  * - transform: string like "w_800,h_800,c_limit"
//  */
// function cloudinaryTransform(url, transform) {
//   if (!transform || !url) return url;
//   // naive insertion: replace "/upload/" with "/upload/<transform>/"
//   return url.replace("/upload/", `/upload/${transform}/`);
// }

// /**
//  * postImageToAI
//  * Accepts a `file` object:
//  *  - multer memory: { buffer, originalname, mimetype }
//  *  - cloudinary result (multer-storage-cloudinary): { secure_url, originalname, mimetype, path, url }
//  */
// async function postImageToAI(endpoint, file, options = {}) {
//   // options: { cloudinaryTransform: "w_512,h_512,c_limit" }
//   let buffer;
//   let filename = file?.originalname || `upload-${Date.now()}.jpg`;
//   let contentType = file?.mimetype || "image/jpeg";

//   console.log(`🔧 Calling Vision AI: ${AI_BASE}${endpoint}`);

//   if (file?.buffer) {
//     buffer = file.buffer;
//   } else {
//     // try common Cloudinary keys
//     const url = file?.secure_url || file?.url || file?.path || file?.public_url;
//     if (!url) throw new Error("No file buffer and no accessible file URL in request");

//     // optionally shrink using Cloudinary transformation to reduce bytes
//     const fetchUrl = options.cloudinaryTransform ? cloudinaryTransform(url, options.cloudinaryTransform) : url;
//     buffer = await _fetchBytesFromUrl(fetchUrl);

//     // derive filename from URL if not present
//     if (!file.originalname) {
//       const parts = fetchUrl.split("/");
//       filename = parts[parts.length - 1].split("?")[0];
//     }
//   }

//   // Build form-data
//   const form = new FormData();
//   // Microservice expects field named `image`
//   form.append("image", buffer, { filename, contentType });

//   const headers = {
//     ...form.getHeaders(),
//     ...(AI_API_KEY ? { "x-api-key": AI_API_KEY } : {}),
//   };

//   const url = `${AI_BASE}${endpoint}`;
//   try {
//     const resp = await axios.post(url, form, {
//       headers,
//       timeout: 120000, // 120s
//     });
//     return resp.data;
//   } catch (err) {
//     console.error(`❌ Vision AI Error for ${endpoint}:`, err?.response?.data || err.message);
//     // Wrap error to include remote response if present
//     const remote = err?.response?.data || err?.response?.statusText || err.message;
//     throw new Error(`AI service request failed: ${JSON.stringify(remote)}`);
//   }
// }

// // Exports: wrappers for each AI endpoint (match microservice routes)
// module.exports = {
//   generateStory: (file, opts) => postImageToAI("/vision/generate_story", file, opts),
//   similarCrafts: (file, opts) => postImageToAI("/vision/similar_crafts", file, opts),
//   priceSuggestion: (file, opts) => postImageToAI("/vision/price_suggestion", file, opts),
//   complementaryProducts: (file, opts) => postImageToAI("/vision/complementary_products", file, opts),
//   purchaseAnalysis: (file, opts) => postImageToAI("/vision/purchase_analysis", file, opts),
//   fraudDetection: (file, opts) => postImageToAI("/vision/fraud_detection", file, opts),
//   orderFulfillment: (file, opts) => postImageToAI("/vision/order_fulfillment_analysis", file, opts),
//   qualityPredictions: (file, opts) => postImageToAI("/vision/quality_predictions", file, opts),
// };


// backend/src/services/visionAI.js

const axios = require("axios");
const FormData = require("form-data");

// Vision AI service configuration
const AI_BASE = process.env.AI_SERVICES_URL || "https://orchid-genai.azurewebsites.net";
const AI_API_KEY = process.env.AI_SERVICE_KEY || "";

console.log(`🔧 Vision AI Service URL: ${AI_BASE}`);
console.log(`🔐 API Key configured: ${AI_API_KEY ? 'Yes' : 'No'}`);

/**
 * Fetch raw bytes from an accessible URL (Cloudinary secure_url)
 */
async function _fetchBytesFromUrl(url) {
  try {
    const resp = await axios.get(url, {
      responseType: "arraybuffer",
      timeout: 120000, // 120s timeout
    });
    return Buffer.from(resp.data);
  } catch (error) {
    console.error(`Failed to fetch image from URL: ${url}`, error.message);
    throw new Error(`Image fetch failed: ${error.message}`);
  }
}

/**
 * Apply Cloudinary transformation to reduce payload
 */
function cloudinaryTransform(url, transform) {
  if (!transform || !url) return url;
  return url.replace("/upload/", `/upload/${transform}/`);
}

/**
 * Post image to AI service
 */
async function postImageToAI(endpoint, file, options = {}) {
  let buffer;
  let filename = file?.originalname || `upload-${Date.now()}.jpg`;
  let contentType = file?.mimetype || "image/jpeg";

  console.log(`📤 Calling Vision AI: ${AI_BASE}${endpoint}`);

  // Handle different file sources
  if (file?.buffer) {
    buffer = file.buffer;
  } else {
    const url = file?.secure_url || file?.url || file?.path || file?.public_url;
    if (!url) {
      throw new Error("No file buffer and no accessible file URL in request");
    }

    const fetchUrl = options.cloudinaryTransform 
      ? cloudinaryTransform(url, options.cloudinaryTransform) 
      : url;
    
    buffer = await _fetchBytesFromUrl(fetchUrl);

    if (!file.originalname) {
      const parts = fetchUrl.split("/");
      filename = parts[parts.length - 1].split("?")[0];
    }
  }

  // Build form-data
  const form = new FormData();
  form.append("image", buffer, { filename, contentType });

  const headers = {
    ...form.getHeaders(),
    ...(AI_API_KEY ? { "x-api-key": AI_API_KEY } : {}),
  };

  const url = `${AI_BASE}${endpoint}`;
  
  try {
    const resp = await axios.post(url, form, {
      headers,
      timeout: 300000, // 300s (5 min) timeout for AI processing - matches backend timeout
      maxContentLength: Infinity,
      maxBodyLength: Infinity,
    });
    
    console.log(`✅ Vision AI response from ${endpoint}: ${resp.status}`);
    return resp.data;
    
  } catch (err) {
    const errorMsg = err?.response?.data?.detail || err?.response?.data?.message || err.message;
    const statusCode = err?.response?.status || 'N/A';
    console.error(`❌ Vision AI Error for ${endpoint} (${statusCode}):`, errorMsg);
    
    throw new Error(`Vision AI request failed: ${errorMsg}`);
  }
}

// FIXED: Use hyphenated endpoints (matching what the backend expects and what vision_routes_fixed.py provides)
module.exports = {
  generateStory: (file, opts) => postImageToAI("/vision/generate-story", file, opts),
  similarCrafts: (file, opts) => postImageToAI("/vision/similar-crafts", file, opts),
  priceSuggestion: (file, opts) => postImageToAI("/vision/price-suggestion", file, opts),
  complementaryProducts: (file, opts) => postImageToAI("/vision/complementary-products", file, opts),
  purchaseAnalysis: (file, opts) => postImageToAI("/vision/purchase-analysis", file, opts),
  fraudDetection: (file, opts) => postImageToAI("/vision/fraud-detection", file, opts),
  orderFulfillment: (file, opts) => postImageToAI("/vision/order-fulfillment-analysis", file, opts),
  qualityPredictions: (file, opts) => postImageToAI("/vision/quality-predictions", file, opts),
};