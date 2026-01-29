const express = require("express");
const dotenv = require("dotenv");
const cookieParser = require("cookie-parser");
const cors = require("cors");

// Configs
const database = require("./config/database");
const { cloudinaryConnect } = require("./config/cloudinary");

// Routes
const authRoutes = require("./routes/authRoutes");
const userRoutes = require("./routes/userRoutes");
const artworkRoutes = require("./routes/artworkRoutes");
const orderRoutes = require("./routes/orderRoutes");
const likeRoutes = require("./routes/likeRoutes");
const cartRoutes = require("./routes/cartRoutes");
const visionRoutes = require("./routes/visionRoutes");
const giftAIRoutes = require("./routes/giftAIRoutes");

// Initialize app
dotenv.config();
const app = express();
const PORT = process.env.PORT || 5000;

// ------------------- Database & Cloudinary -------------------
database.connect();
cloudinaryConnect();

// ------------------- Middlewares -------------------
app.use(express.json());
app.use(cookieParser());

// Handle preflight requests
app.options('*', (req, res) => {
  res.header('Access-Control-Allow-Origin', req.headers.origin || '*');
  res.header('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS,PATCH');
  res.header('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With,Accept,Origin');
  res.header('Access-Control-Allow-Credentials', 'true');
  res.sendStatus(200);
});

app.use(
  cors({
    origin: true, // Allow all origins for now to debug
    credentials: true,
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
    exposedHeaders: ["Set-Cookie"],
    optionsSuccessStatus: 200
  })
);

// ------------------- Routes -------------------
app.use("/api/v1/auth", authRoutes);
app.use("/api/v1/user", userRoutes);
app.use("/api/v1/artworks", artworkRoutes);
app.use("/api/v1/order", orderRoutes);
app.use("/api/v1/like", likeRoutes);
app.use("/api/v1/cart", cartRoutes);
app.use("/api/v1/vision", visionRoutes);
app.use("/api/v1/gift-ai", giftAIRoutes);

// ------------------- Health Check -------------------
app.get("/", (req, res) => {
  return res.json({
    success: true,
    message: "Your server is running",
    timestamp: new Date().toISOString(),
    environment: {
      NODE_ENV: process.env.NODE_ENV || "development",
      PORT: PORT,
      FRONTEND_URL: process.env.FRONTEND_URL || "Not set",
      GIFT_AI_SERVICE_URL: process.env.GIFT_AI_SERVICE_URL || "Not set",
      VISION_AI_SERVICE_URL: process.env.VISION_AI_SERVICE_URL || "Not set"
    }
  });
});

// Test endpoint for CORS
app.get("/api/v1/test", (req, res) => {
  res.json({
    success: true,
    message: "CORS test successful",
    origin: req.headers.origin,
    timestamp: new Date().toISOString()
  });
});

// Add a catch-all route for debugging 404s
app.use("*", (req, res) => {
  console.log(`🚫 404 - Route not found: ${req.method} ${req.originalUrl}`);
  console.log(`📍 Available routes:`);
  console.log(`   GET  /`);
  console.log(`   GET  /api/v1/test`);
  console.log(`   *    /api/v1/auth/*`);
  console.log(`   *    /api/v1/user/*`);
  console.log(`   *    /api/v1/artworks/*`);
  console.log(`   *    /api/v1/order/*`);
  console.log(`   *    /api/v1/like/*`);
  console.log(`   *    /api/v1/cart/*`);
  console.log(`   *    /api/v1/vision/*`);
  console.log(`   *    /api/v1/gift-ai/*`);
  
  return res.status(404).json({
    success: false,
    message: `Route ${req.method} ${req.originalUrl} not found`,
    availableRoutes: [
      "GET /",
      "GET /api/v1/test",
      "/api/v1/auth/*",
      "/api/v1/user/*", 
      "/api/v1/artworks/*",
      "/api/v1/order/*",
      "/api/v1/like/*",
      "/api/v1/cart/*",
      "/api/v1/vision/*",
      "/api/v1/gift-ai/*"
    ]
  });
});

// ------------------- Start Server -------------------
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📦 Backend API: Production Server`);
  console.log(`� GFrontend URL: ${process.env.FRONTEND_URL || "Not set"}`);
  console.log(`🎁 Gift AI Service: ${process.env.GIFT_AI_SERVICE_URL || "Not configured"}`);
  console.log(`👁️ Vision AI Service: ${process.env.VISION_AI_SERVICE_URL || "Not configured"}`);
  console.log(`🔧 Environment Variables Check:`);
  console.log(`   - FRONTEND_URL: ${process.env.FRONTEND_URL || "❌ undefined"}`);
  console.log(`   - GIFT_AI_SERVICE_URL: ${process.env.GIFT_AI_SERVICE_URL || "❌ undefined"}`);
  console.log(`   - VISION_AI_SERVICE_URL: ${process.env.VISION_AI_SERVICE_URL || "❌ undefined"}`);
});