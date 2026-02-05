// const express = require("express");
// const dotenv = require("dotenv");
// const cookieParser = require("cookie-parser");
// const cors = require("cors");

// // Configs
// const database = require("./config/database");
// const { cloudinaryConnect } = require("./config/cloudinary");

// // Routes
// const authRoutes = require("./routes/authRoutes");
// const userRoutes = require("./routes/userRoutes");
// const artworkRoutes = require("./routes/artworkRoutes");
// const orderRoutes = require("./routes/orderRoutes");
// const likeRoutes = require("./routes/likeRoutes");
// const cartRoutes = require("./routes/cartRoutes");
// const visionRoutes = require("./routes/visionRoutes");
// const giftAIRoutes = require("./routes/giftAIRoutes");

// // Initialize app
// dotenv.config();
// const app = express();
// const PORT = process.env.PORT || 5000;

// // ------------------- Database & Cloudinary -------------------
// database.connect();
// cloudinaryConnect();

// // ------------------- Middlewares -------------------
// app.use(express.json());
// app.use(cookieParser());

// // ------------------- CORS -------------------

// // const allowedOrigins = [
// //   process.env.FRONTEND_URL,
// //   'https://salmon-pond-08feb7200.6.azurestaticapps.net', // Explicit frontend URL
// //   'http://localhost:3000', // Local development
// //   'http://localhost:5173', // Vite dev server
// //   'https://localhost:3000',
// //   'https://localhost:5173'
// // ];

// // app.use(cors({
// //   origin: function (origin, callback) {
// //     // Allow requests with no origin (mobile apps, curl, etc.)
// //     if (!origin) return callback(null, true);

// //     if (allowedOrigins.includes(origin)) {
// //       return callback(null, true);
// //     } else {
// //       console.log("❌ CORS blocked origin:", origin);
// //       console.log("✅ Allowed origins:", allowedOrigins);
// //       return callback(new Error("Not allowed by CORS"));
// //     }
// //   },
// //   credentials: true,
// //   methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
// //   allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With"],
// // }));

// // app.options("*", cors());


// // Replace the existing CORS configuration with this improved version:

// const allowedOrigins = [
//   process.env.FRONTEND_URL,
//   'https://salmon-pond-08feb7200.6.azurestaticapps.net',
//   'http://localhost:3000',
//   'http://localhost:5173',
//   'https://localhost:3000',
//   'https://localhost:5173'
// ].filter(Boolean); // Remove undefined values

// app.use(cors({
//   origin: function (origin, callback) {
//     // Allow requests with no origin (mobile apps, curl, Postman, etc.)
//     if (!origin) {
//       console.log("✅ Allowing request with no origin");
//       return callback(null, true);
//     }

//     // Check if origin matches any allowed origin or Azure Static Web Apps pattern
//     const isAllowed = allowedOrigins.includes(origin) || 
//                       origin.endsWith('.azurestaticapps.net') ||
//                       origin.includes('localhost');

//     if (isAllowed) {
//       console.log("✅ CORS allowed for origin:", origin);
//       return callback(null, true);
//     } else {
//       console.log("❌ CORS blocked origin:", origin);
//       console.log("📋 Allowed patterns: Azure Static Web Apps, localhost, explicit origins");
//       return callback(null, true); // TEMPORARILY ALLOW ALL FOR DEBUGGING
//       // Change back to this after fixing: return callback(new Error("Not allowed by CORS"));
//     }
//   },
//   credentials: true,
//   methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
//   allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
//   exposedHeaders: ["Content-Length", "X-Request-Id"],
//   maxAge: 86400 // 24 hours
// }));

// // Ensure preflight requests are handled
// app.options("*", cors());

// // ------------------- Routes -------------------
// app.use("/api/v1/auth", authRoutes);
// app.use("/api/v1/user", userRoutes);
// app.use("/api/v1/artworks", artworkRoutes);
// app.use("/api/v1/order", orderRoutes);
// app.use("/api/v1/like", likeRoutes);
// app.use("/api/v1/cart", cartRoutes);
// app.use("/api/v1/vision", visionRoutes);
// app.use("/api/v1/gift-ai", giftAIRoutes);

// // ------------------- Health Check -------------------
// app.get("/", (req, res) => {
//   return res.json({
//     success: true,
//     message: "Your server is running",
//     timestamp: new Date().toISOString(),
//     environment: {
//       NODE_ENV: process.env.NODE_ENV || "development",
//       PORT: PORT,
//       FRONTEND_URL: process.env.FRONTEND_URL || "Not set",
//       GIFT_AI_SERVICE_URL: process.env.GIFT_AI_SERVICE_URL || "Not set",
//       VISION_AI_SERVICE_URL: process.env.VISION_AI_SERVICE_URL || "Not set"
//     }
//   });
// });

// // Dedicated health endpoint
// app.get("/health", (req, res) => {
//   return res.json({
//     status: "healthy",
//     timestamp: new Date().toISOString(),
//     uptime: process.uptime(),
//     environment: process.env.NODE_ENV || "development"
//   });
// });

// // Test endpoint for CORS
// app.get("/api/v1/test", (req, res) => {
//   res.json({
//     success: true,
//     message: "CORS test successful",
//     origin: req.headers.origin,
//     timestamp: new Date().toISOString()
//   });
// });

// // Add a catch-all route for debugging 404s
// app.use("*", (req, res) => {
//   console.log(`🚫 404 - Route not found: ${req.method} ${req.originalUrl}`);
//   console.log(`📍 Available routes:`);
//   console.log(`   GET  /`);
//   console.log(`   GET  /api/v1/test`);
//   console.log(`   *    /api/v1/auth/*`);
//   console.log(`   *    /api/v1/user/*`);
//   console.log(`   *    /api/v1/artworks/*`);
//   console.log(`   *    /api/v1/order/*`);
//   console.log(`   *    /api/v1/like/*`);
//   console.log(`   *    /api/v1/cart/*`);
//   console.log(`   *    /api/v1/vision/*`);
//   console.log(`   *    /api/v1/gift-ai/*`);

//   return res.status(404).json({
//     success: false,
//     message: `Route ${req.method} ${req.originalUrl} not found`,
//     availableRoutes: [
//       "GET /",
//       "GET /api/v1/test",
//       "/api/v1/auth/*",
//       "/api/v1/user/*",
//       "/api/v1/artworks/*",
//       "/api/v1/order/*",
//       "/api/v1/like/*",
//       "/api/v1/cart/*",
//       "/api/v1/vision/*",
//       "/api/v1/gift-ai/*"
//     ]
//   });
// });

// // ------------------- Start Server -------------------
// app.listen(PORT, () => {
//   console.log(`🚀 Server running on port ${PORT}`);
//   console.log(`📦 Backend API: Production Server`);
//   console.log(`� GFrontend URL: ${process.env.FRONTEND_URL || "Not set"}`);
//   console.log(`🎁 Gift AI Service: ${process.env.GIFT_AI_SERVICE_URL || "Not configured"}`);
//   console.log(`👁️ Vision AI Service: ${process.env.VISION_AI_SERVICE_URL || "Not configured"}`);
//   console.log(`🔧 Environment Variables Check:`);
//   console.log(`   - FRONTEND_URL: ${process.env.FRONTEND_URL || "❌ undefined"}`);
//   console.log(`   - GIFT_AI_SERVICE_URL: ${process.env.GIFT_AI_SERVICE_URL || "❌ undefined"}`);
//   console.log(`   - VISION_AI_SERVICE_URL: ${process.env.VISION_AI_SERVICE_URL || "❌ undefined"}`);
// });



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

// ------------------- CORS -------------------
const allowedOrigins = [
  process.env.FRONTEND_URL,
  'https://salmon-pond-08feb7200.6.azurestaticapps.net',
  'http://localhost:3000',
  'http://localhost:5173',
  'https://localhost:3000',
  'https://localhost:5173'
].filter(Boolean);

app.use(cors({
  origin: function (origin, callback) {
    if (!origin) {
      return callback(null, true);
    }

    const isAllowed = allowedOrigins.some(allowedOrigin => origin === allowedOrigin) || 
                      origin.endsWith('.azurestaticapps.net') ||
                      /^https?:\/\/localhost(:\d+)?$/.test(origin);

    if (isAllowed) {
      return callback(null, true);
    } else {
      return callback(new Error("Not allowed by CORS"));
    }
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
  allowedHeaders: ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
  exposedHeaders: ["Content-Length", "X-Request-Id"],
  maxAge: 86400,
  preflightContinue: false,
  optionsSuccessStatus: 204
}));

app.options("*", cors());

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

app.get("/health", (req, res) => {
  return res.json({
    status: "healthy",
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    environment: process.env.NODE_ENV || "development"
  });
});

app.get("/api/v1/test", (req, res) => {
  res.json({
    success: true,
    message: "CORS test successful",
    origin: req.headers.origin,
    timestamp: new Date().toISOString()
  });
});

app.use("*", (req, res) => {
  return res.status(404).json({
    success: false,
    message: `Route ${req.method} ${req.originalUrl} not found`,
    availableRoutes: [
      "GET /",
      "GET /health",
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
  console.log(`📦 Environment: ${process.env.NODE_ENV || "development"}`);
  console.log(`🌐 Frontend URL: ${process.env.FRONTEND_URL || "Not set"}`);
  console.log(`🎁 Gift AI Service: ${process.env.GIFT_AI_SERVICE_URL || "Not configured"}`);
  console.log(`👁️ Vision AI Service: ${process.env.VISION_AI_SERVICE_URL || "Not configured"}`);
});