const express = require("express");
const dotenv = require("dotenv");
const cookieParser = require("cookie-parser");
const cors = require("cors");
// const fileUpload = require("express-fileupload");

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
    origin: process.env.FRONTEND_URL || "*",
    credentials: true,
  })
);
// app.use(
//   fileUpload({
//     useTempFiles: true,
//     tempFileDir: "/tmp/",
//   })
// );

// ------------------- Routes -------------------
app.use("/api/v1/auth", authRoutes);
app.use("/api/v1/user", userRoutes);
app.use("/api/v1/artworks", artworkRoutes);
app.use("/api/v1/order", orderRoutes);
app.use("/api/v1/like", likeRoutes);
app.use("/api/v1/cart", cartRoutes);
app.use("/api/v1/vision", visionRoutes);

// ------------------- Health Check -------------------
app.get("/", (req, res) => {
  return res.json({
    success: true,
    message: "Your server is running",
  });
});

// ------------------- Start Server -------------------
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
