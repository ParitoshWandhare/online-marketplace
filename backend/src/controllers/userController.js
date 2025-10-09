const User = require("../models/User");
const mongoose = require("mongoose");
const Artwork = require("../models/Artwork");
const Order = require("../models/Order");

// ------------------ GET PROFILE ------------------
exports.getProfile = async (req, res) => {
  try {
    const userId = req.user.id;

    const user = await User.findById(userId)
      .select("-password")
      .populate("likes", "title price media");

    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ success: true, user });
  } catch (err) {
    console.error("Error in getProfile:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ UPDATE PROFILE ------------------
exports.updateProfile = async (req, res) => {
  try {
    const userId = req.user.id;
    const { name, phone, avatarUrl, bio, region } = req.body;

    const user = await User.findByIdAndUpdate(
      userId,
      {
        $set: {
          name,
          phone,
          avatarUrl,
          bio,
          region,
          lastSeen: new Date(),
        },
      },
      { new: true }
    ).select("-password");

    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ success: true, message: "Profile updated", user });
  } catch (err) {
    console.error("Error in updateProfile:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ DELETE ACCOUNT ------------------
exports.deleteAccount = async (req, res) => {
  try {
    const userId = req.user.id;

    const user = await User.findByIdAndDelete(userId);
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ success: true, message: "Account deleted successfully" });
  } catch (err) {
    console.error("Error in deleteAccount:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ GET SELLER STATS ------------------
exports.getSellerStats = async (req, res) => {
  try {
    const sellerId = req.user.id;

    // 1. Total unique products by this seller
    const totalProducts = await Artwork.countDocuments({ artistId: sellerId });

    // 2. Last 30 days filter
    const lastMonth = new Date();
    lastMonth.setDate(lastMonth.getDate() - 30);

    // 3. Aggregation: only include PAID orders, then unwind items
    const stats = await Order.aggregate([
      { $match: { createdAt: { $gte: lastMonth } } },
      { $unwind: "$items" },
      {
        $match: {
          // Handle both ObjectId and string storage
          $expr: {
            $eq: [
              "$items.sellerId",
              mongoose.Types.ObjectId.isValid(sellerId)
                ? new mongoose.Types.ObjectId(sellerId)
                : sellerId,
            ],
          },
        },
      },
      {
        $group: {
          _id: null,
          totalOrders: { $sum: 1 }, // count each item as an order line
          totalRevenue: {
            $sum: { $multiply: ["$items.qty", "$items.unitPrice"] },
          },
        },
      },
    ]);

    res.json({
      success: true,
      stats: {
        totalProducts,
        totalOrders: stats[0]?.totalOrders || 0,
        totalRevenue: stats[0]?.totalRevenue || 0,
      },
    });
  } catch (err) {
    console.error("Error in getSellerStats:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching seller stats",
      error: err.message,
    });
  }
};