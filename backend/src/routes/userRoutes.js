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


// ADDRESS MANAGEMENT ROUTES


// Get all addresses for current user
router.get('/addresses', authMiddleware, userController.getAddresses);

// Get default address
router.get('/addresses/default', authMiddleware, userController.getDefaultAddress);

// Get specific address
router.get('/addresses/:addressId', authMiddleware, userController.getAddressById);

// Add new address
router.post('/addresses', authMiddleware, userController.addAddress);

// Update address
router.put('/addresses/:addressId', authMiddleware, userController.updateAddress);

// Delete address
router.delete('/addresses/:addressId', authMiddleware, userController.deleteAddress);

// Set default address
router.patch('/addresses/:addressId/set-default', authMiddleware, userController.setDefaultAddress);


module.exports = router;
