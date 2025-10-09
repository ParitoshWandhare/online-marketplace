const mongoose = require("mongoose");
const crypto = require("crypto");
const Cart = require("../models/Cart");
const Artwork = require("../models/Artwork");
const Order = require("../models/Order");
const { instance } = require("../config/razorpay");

// ------------------ ADD TO CART ------------------
exports.addToCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId } = req.body;
    let qty = parseInt(req.body.qty, 10);
    if (!artworkId) return res.status(400).json({ success: false, message: "artworkId is required" });
    if (Number.isNaN(qty) || qty <= 0) qty = 1;

    // check artwork
    const artwork = await Artwork.findById(artworkId);
    if (!artwork || artwork.status !== "published") {
      return res.status(404).json({ success: false, message: "Artwork not available" });
    }

    // find/create cart
    let cart = await Cart.findOne({ userId });
    if (!cart) cart = new Cart({ userId, items: [] });

    const existingItem = cart.items.find((it) => it.artworkId.toString() === artworkId.toString());
    if (existingItem) existingItem.qty += qty;
    else cart.items.push({ artworkId: new mongoose.Types.ObjectId(artworkId), qty });

    await cart.save();
    await cart.populate("items.artworkId");

    const total = cart.items.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0);

    res.json({ success: true, message: "Cart updated", cart, total });
  } catch (err) {
    console.error("Error in addToCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ REMOVE FROM CART ------------------
exports.removeFromCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId } = req.params;

    let cart = await Cart.findOneAndUpdate(
      { userId },
      { $pull: { items: { artworkId: artworkId } } },
      { new: true }
    ).populate("items.artworkId");

    if (!cart) cart = { items: [] };

    const total = cart.items?.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0) || 0;

    res.json({ success: true, message: "Item removed from cart", cart, total });
  } catch (err) {
    console.error("Error in removeFromCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ GET CART ------------------
exports.getCart = async (req, res) => {
  try {
    const userId = req.user.id;
    let cart = await Cart.findOne({ userId }).populate("items.artworkId");

    if (!cart) {
      return res.json({ success: true, message: "Cart is empty", cart: { items: [] }, total: 0 });
    }

    const total = cart.items.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0);

    res.json({ success: true, cart, total });
  } catch (err) {
    console.error("Error in getCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ UPDATE CART ITEM QUANTITY ------------------
exports.updateCartItem = async (req, res) => {
  try {
    const userId = req.user.id;
    const { artworkId, qty } = req.body;

    if (!artworkId || qty === undefined) {
      return res.status(400).json({ success: false, message: "artworkId and qty are required" });
    }
    if (qty < 1) {
      return res.status(400).json({ success: false, message: "Quantity must be at least 1" });
    }

    let cart = await Cart.findOne({ userId });
    if (!cart) return res.status(404).json({ success: false, message: "Cart not found" });

    const item = cart.items.find((it) => it.artworkId.toString() === artworkId);
    if (!item) return res.status(404).json({ success: false, message: "Item not in cart" });

    item.qty = qty;
    await cart.save();
    await cart.populate("items.artworkId");

    const total = cart.items.reduce((sum, item) => sum + (item.artworkId?.price || 0) * item.qty, 0);

    res.json({ success: true, message: "Cart updated", cart, total });
  } catch (err) {
    console.error("Error in updateCartItem:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ CREATE ORDER FROM CART ------------------
exports.createOrderFromCart = async (req, res) => {
  try {
    const userId = req.user.id;
    const cart = await Cart.findOne({ userId }).populate("items.artworkId");

    if (!cart || cart.items.length === 0) {
      return res.status(400).json({ success: false, message: "Cart is empty" });
    }

    // group by seller
    const groups = {};
    for (const item of cart.items) {
      const sellerId = item.artworkId.artistId.toString();
      if (!groups[sellerId]) groups[sellerId] = [];
      groups[sellerId].push(item);
    }

    const created = [];
    for (const sellerId of Object.keys(groups)) {
      const groupItems = groups[sellerId];
      let total = 0;
      let orderItems = [];

      for (const item of groupItems) {
        if (item.artworkId.quantity < item.qty) {
          return res.status(400).json({
            success: false,
            message: `Not enough stock for ${item.artworkId.title}`,
          });
        }

        orderItems.push({
          artworkId: item.artworkId._id,
          titleCopy: item.artworkId.title,
          qty: item.qty,
          unitPrice: item.artworkId.price,
          currency: item.artworkId.currency,
          sellerId: item.artworkId.artistId, // add sellerId here
        });

        total += item.artworkId.price * item.qty;
      }

      const shortUserId = userId.toString().slice(-6);
      const shortSellerId = sellerId.toString().slice(-6);

      const razorpayOrder = await instance.orders.create({
        amount: total * 100,
        currency: "INR",
        receipt: `cart_${shortUserId}_${shortSellerId}_${Date.now()}`.slice(0, 39), // ensure <40
      });

      const order = await Order.create({
        buyerId: userId,
        sellerId,
        items: orderItems,
        total,
        currency: "INR",
        razorpayOrderId: razorpayOrder.id,
        status: "created",
      });

      created.push({ orderId: order._id, sellerId, order, razorpayOrder });
    }

    cart.items = [];
    await cart.save();

    res.status(201).json({ success: true, created });
  } catch (err) {
    console.error("Error in createOrderFromCart:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};

// ------------------ VERIFY CART PAYMENT ------------------
exports.verifyCartPayment = async (req, res) => {
  try {
    const { razorpayOrderId, razorpayPaymentId, razorpaySignature, orderId } = req.body;

    const body = razorpayOrderId + "|" + razorpayPaymentId;
    const expectedSignature = crypto
      .createHmac("sha256", process.env.RAZORPAY_SECRET)
      .update(body.toString())
      .digest("hex");

    if (expectedSignature !== razorpaySignature) {
      return res.status(400).json({ success: false, message: "Payment verification failed" });
    }

    const order = await Order.findById(orderId);
    if (!order) {
      return res.status(404).json({ success: false, message: "Order not found" });
    }

    if (order.razorpayOrderId !== razorpayOrderId) {
      return res.status(400).json({ success: false, message: "Order ID mismatch" });
    }

    // Update order with payment details
    order.razorpayPaymentId = razorpayPaymentId;
    order.razorpaySignature = razorpaySignature;
    order.status = "paid";
    await order.save();

    // reduce stock
    for (const item of order.items) {
      const updatedArtwork = await Artwork.findByIdAndUpdate(
        item.artworkId,
        { $inc: { quantity: -item.qty } },
        { new: true }
      );
      if (updatedArtwork && updatedArtwork.quantity === 0) {
        updatedArtwork.status = "out_of_stock";
        await updatedArtwork.save();
      }
    }

    res.json({ success: true, message: "Cart payment verified", order });
  } catch (err) {
    console.error("Error in verifyCartPayment:", err);
    res.status(500).json({ success: false, message: "Internal server error", error: err.message });
  }
};