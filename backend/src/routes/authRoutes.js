// backend/src/routes/authRoutes.js
const express = require("express");
const router = express.Router();
const authController = require("../controllers/authController");
const authMiddleware = require("../middlewares/authMiddleware");

// Signup/login flow
router.post("/send-otp", authController.sendOtp);
router.post("/signup", authController.signup);
router.post("/login", authController.login);

// Protected route to fetch profile
router.get("/profile", authMiddleware, authController.profile);

module.exports = router;
