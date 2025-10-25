// backend/src/controllers/orderController.js
const { instance } = require("../config/razorpay");
const Order = require("../models/Order");
const Artwork = require("../models/Artwork");
const crypto = require("crypto");

// Helper function to validate address
const validateAddress = (address) => {
  const required = ['fullName', 'phone', 'addressLine1', 'city', 'state', 'pincode'];
  for (const field of required) {
    if (!address[field]) {
      return { valid: false, message: `${field} is required in shipping address` };
    }
  }
  return { valid: true };
};

// ------------------ CREATE ORDER (Multi-Seller) ------------------
exports.createOrder = async (req, res) => {
  try {
    const { items, shippingAddress } = req.body;
    const buyerId = req.user.id;

    if (!items || !Array.isArray(items) || items.length === 0) {
      return res.status(400).json({ success: false, message: "No items in order" });
    }

    // Validate shipping address
    if (!shippingAddress) {
      return res.status(400).json({ success: false, message: "Shipping address is required" });
    }

    const addressValidation = validateAddress(shippingAddress);
    if (!addressValidation.valid) {
      return res.status(400).json({ success: false, message: addressValidation.message });
    }

    // Group items by seller
    const sellersMap = new Map();
    for (const item of items) {
      if (!sellersMap.has(item.sellerId.toString())) {
        sellersMap.set(item.sellerId.toString(), []);
      }
      sellersMap.get(item.sellerId.toString()).push(item);
    }

    const createdOrders = [];

    // Create a separate order and Razorpay transaction for each seller
    for (const [sellerId, sellerItems] of sellersMap.entries()) {
      let total = 0;
      let orderItems = [];

      for (const item of sellerItems) {
        const artwork = await Artwork.findById(item.artworkId);
        
        if (!artwork || artwork.status !== "published") {
          return res.status(404).json({
            success: false,
            message: `Artwork ${item.artworkId} not available`,
          });
        }

        if (artwork.quantity < item.qty) {
          return res.status(400).json({
            success: false,
            message: `Not enough stock for ${artwork.title}`,
          });
        }
        
        orderItems.push({
          artworkId: artwork._id,
          sellerId: artwork.artistId,
          titleCopy: artwork.title,
          qty: item.qty,
          unitPrice: artwork.price,
          currency: artwork.currency,
        });

        total += artwork.price * item.qty;
      }

      const roundedTotal = Math.round(total * 100);

      const razorpayOrder = await instance.orders.create({
        amount: roundedTotal,
        currency: "INR",
        receipt: `receipt_${Date.now()}`,
      });

      const order = await Order.create({
        buyerId,
        items: orderItems,
        total,
        currency: "INR",
        shippingAddress,
        razorpayOrderId: razorpayOrder.id,
        status: "created",
      });

      createdOrders.push({
        sellerId,
        order,
        razorpayOrder,
      });
    }

    res.status(201).json({ success: true, created: createdOrders });
  } catch (err) {
    console.error("Error in createOrder:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ VERIFY PAYMENT ------------------
exports.verifyPayment = async (req, res) => {
  try {
    const { razorpayOrderId, razorpayPaymentId, razorpaySignature } = req.body;
    
    if (!razorpayOrderId || !razorpayPaymentId || !razorpaySignature) {
      return res.status(400).json({ success: false, message: "Missing payment verification data." });
    }

    const body = razorpayOrderId + "|" + razorpayPaymentId;
    
    const razorpaySecret = process.env.RAZORPAY_SECRET;
    if (!razorpaySecret) {
      console.error("RAZORPAY_SECRET is not set in environment variables.");
      return res.status(500).json({ success: false, message: "Server configuration error." });
    }

    const expectedSignature = crypto
      .createHmac("sha256", razorpaySecret)
      .update(body.toString())
      .digest("hex");

    if (expectedSignature !== razorpaySignature) {
      console.error("Payment signature mismatch. Expected:", expectedSignature, "Received:", razorpaySignature);
      return res.status(400).json({ success: false, message: "Payment verification failed" });
    }

    const order = await Order.findOneAndUpdate(
      { razorpayOrderId },
      { 
        razorpayPaymentId, 
        razorpaySignature, 
        status: "paid"
      },
      { new: true }
    ).populate('items.artworkId').populate('items.sellerId', 'name email avatarUrl');

    if (order) {
      for (const item of order.items) {
        const updatedArtwork = await Artwork.findByIdAndUpdate(
          item.artworkId._id,
          { $inc: { quantity: -item.qty } },
          { new: true }
        );

        if (updatedArtwork && updatedArtwork.quantity <= 0) {
          updatedArtwork.status = "out_of_stock";
          await updatedArtwork.save();
        }
      }
    }

    res.json({ success: true, message: "Payment verified", order });
  } catch (err) {
    console.error("Error in verifyPayment:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ GET MY ORDERS (BUYER) ------------------
exports.getMyOrders = async (req, res) => {
  try {
    const buyerId = req.user.id;
    const orders = await Order.find({ buyerId })
      .populate("items.artworkId")
      .populate("items.sellerId", "name email avatarUrl")
      .sort({ createdAt: -1 });

    res.json({ success: true, count: orders.length, orders });
  } catch (err) {
    console.error("Error in getMyOrders:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while getting my orders",
    });
  }
};

// ------------------ GET SALES (SELLER) ------------------
exports.getSales = async (req, res) => {
  try {
    const sellerId = req.user.id;
    const sales = await Order.find({ "items.sellerId": sellerId })
      .populate("items.artworkId")
      .populate("buyerId", "name email avatarUrl")
      .sort({ createdAt: -1 });

    res.json({ success: true, count: sales.length, sales });
  } catch (err) {
    console.error("Error in getSales:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while getting sales",
    });
  }
};

// ------------------ UPDATE ORDER STATUS (Seller only) ------------------
exports.updateOrderStatus = async (req, res) => {
  try {
    const { id } = req.params;
    const { artworkId, status, trackingNumber } = req.body;
    const sellerId = req.user.id;

    const order = await Order.findById(id);
    if (!order) {
      return res.status(404).json({ success: false, message: "Order not found" });
    }

    const item = order.items.find(
      (it) =>
        it.artworkId.toString() === artworkId &&
        it.sellerId.toString() === sellerId
    );

    if (!item) {
      return res.status(403).json({ success: false, message: "Unauthorized or item not found" });
    }

    order.status = status;
    
    // Add tracking info if provided
    if (trackingNumber) {
      order.trackingNumber = trackingNumber;
    }

    // Set shipped/delivered timestamps
    if (status === "shipped" && !order.shippedAt) {
      order.shippedAt = new Date();
    }
    if (status === "delivered" && !order.deliveredAt) {
      order.deliveredAt = new Date();
    }

    await order.save();

    res.json({ success: true, message: "Order status updated", order });
  } catch (err) {
    console.error("Error in updateOrderStatus:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while updating order status",
    });
  }
};

// ------------------ CREATE DIRECT ORDER ------------------
exports.createDirectOrder = async (req, res) => {
  try {
    const { artworkId, qty, shippingAddress } = req.body;
    const buyerId = req.user.id;

    if (!artworkId || !qty) {
      return res.status(400).json({ success: false, message: "Artwork ID and quantity are required." });
    }

    // Validate shipping address
    if (!shippingAddress) {
      return res.status(400).json({ success: false, message: "Shipping address is required" });
    }

    const addressValidation = validateAddress(shippingAddress);
    if (!addressValidation.valid) {
      return res.status(400).json({ success: false, message: addressValidation.message });
    }
    
    const artwork = await Artwork.findById(artworkId);

    if (!artwork || artwork.status !== "published") {
      return res.status(404).json({ success: false, message: "Artwork not available for purchase." });
    }

    if (artwork.quantity < qty) {
      return res.status(400).json({ success: false, message: "Not enough stock available." });
    }
    
    const total = artwork.price * qty;

    const razorpayOrder = await instance.orders.create({
      amount: total * 100,
      currency: "INR",
      receipt: `receipt_${Date.now()}`,
    });

    const newOrder = await Order.create({
      buyerId,
      items: [{
        artworkId: artwork._id,
        sellerId: artwork.artistId,
        titleCopy: artwork.title,
        qty,
        unitPrice: artwork.price,
        currency: artwork.currency,
      }],
      total,
      currency: "INR",
      shippingAddress,
      razorpayOrderId: razorpayOrder.id,
      status: "created",
    });

    res.status(201).json({ success: true, order: newOrder, razorpayOrder });
    
  } catch (err) {
    console.error("Error creating direct order:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};