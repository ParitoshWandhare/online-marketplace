const express = require("express");
const router = express.Router();
const cartController = require("../controllers/cartController");
const authMiddleware = require("../middlewares/authMiddleware");

router.post("/add", authMiddleware, cartController.addToCart);
router.get("/", authMiddleware, cartController.getCart);
router.put("/update", authMiddleware, cartController.updateCartItem);
router.delete("/remove/:artworkId", authMiddleware, cartController.removeFromCart);
router.post("/checkout", authMiddleware, cartController.createOrderFromCart);
router.post("/verify", authMiddleware, cartController.verifyCartPayment);

module.exports = router;
