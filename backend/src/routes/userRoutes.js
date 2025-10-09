const express = require("express");
const router = express.Router();
const userController = require("../controllers/userController");
const authMiddleware = require("../middlewares/authMiddleware");

// Get logged-in user's profile
router.get("/me", authMiddleware, userController.getProfile);

// Update logged-in user's profile
router.put("/update", authMiddleware, userController.updateProfile);

// Delete logged-in user's account
router.delete("/delete", authMiddleware, userController.deleteAccount);

// Get seller stats
router.get("/stats", authMiddleware, userController.getSellerStats);

module.exports = router;
