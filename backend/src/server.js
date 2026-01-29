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
app.use(
  cors({
    origin: [
      process.env.FRONTEND_URL?.replace(/\/$/, ''), // Remove trailing slash if present
      process.env.FRONTEND_URL, // Keep original as fallback
      'https://salmon-pond-08feb7200.6.azurestaticapps.net', // Explicit frontend URL
      'http://localhost:5173', // Local development
      'http://localhost:3000'  // Alternative local port
    ].filter(Boolean), // Remove any undefined values
    credentials: true,                // allow cookies / auth headers
    methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allowedHeaders: ["Content-Type", "Authorization"],
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
  });
});

// ------------------- Start Server -------------------
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`📦 Backend API: http://localhost:${PORT}`);
  console.log(`🎁 Gift AI Service: ${process.env.GIFT_AI_SERVICE_URL || "http://localhost:8001"}`);
  //console.log(`👁️ Vision AI Service: ${process.env.VISION_AI_SERVICE_URL || "http://localhost:8001"}`);
});