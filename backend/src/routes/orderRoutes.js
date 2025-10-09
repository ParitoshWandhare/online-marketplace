const express = require("express");
const router = express.Router();
const orderController = require("../controllers/orderController");
const authMiddleware = require("../middlewares/authMiddleware");

// Create new order
router.post("/create", authMiddleware, orderController.createOrder);

// Verify payment
router.post("/verify", authMiddleware, orderController.verifyPayment);

// Buyer: My orders
router.get("/my-orders", authMiddleware, orderController.getMyOrders);

// Seller: My sales
router.get("/my-sales", authMiddleware, orderController.getSales);

// Seller: Update order status
router.put("/:id/status", authMiddleware, orderController.updateOrderStatus);

// New route for a direct "Buy Now" order
router.post("/direct", authMiddleware, orderController.createDirectOrder);

module.exports = router;
