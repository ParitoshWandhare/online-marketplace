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

    const totalProducts = await Artwork.countDocuments({ artistId: sellerId });

    const lastMonth = new Date();
    lastMonth.setDate(lastMonth.getDate() - 30);

    const stats = await Order.aggregate([
      { $match: { createdAt: { $gte: lastMonth } } },
      { $unwind: "$items" },
      {
        $match: {
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
          totalOrders: { $sum: 1 },
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

// ========================================================================
// ADDRESS CRUD OPERATIONS
// ========================================================================

// ------------------ GET ALL ADDRESSES ------------------
exports.getAddresses = async (req, res) => {
  try {
    const userId = req.user.id;

    const user = await User.findById(userId).select("addresses");
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({ 
      success: true, 
      count: user.addresses.length,
      addresses: user.addresses 
    });
  } catch (err) {
    console.error("Error in getAddresses:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ GET SINGLE ADDRESS ------------------
exports.getAddressById = async (req, res) => {
  try {
    const userId = req.user.id;
    const { addressId } = req.params;

    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    const address = user.addresses.id(addressId);
    
    if (!address) {
      return res.status(404).json({ success: false, message: "Address not found" });
    }

    res.json({ success: true, address });
  } catch (err) {
    console.error("Error in getAddressById:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ ADD NEW ADDRESS ------------------
exports.addAddress = async (req, res) => {
  try {
    const userId = req.user.id;
    const { label, fullName, phone, addressLine1, addressLine2, city, state, pincode, country, landmark, isDefault } = req.body;

    // Validate required fields
    if (!label || !fullName || !phone || !addressLine1 || !city || !state || !pincode) {
      return res.status(400).json({ 
        success: false, 
        message: "Missing required fields: label, fullName, phone, addressLine1, city, state, pincode" 
      });
    }

    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    // If this is set as default, unset other defaults
    if (isDefault) {
      user.addresses.forEach(addr => {
        addr.isDefault = false;
      });
    }

    // If this is the first address, make it default
    const makeDefault = isDefault || user.addresses.length === 0;

    const newAddress = {
      label,
      fullName,
      phone,
      addressLine1,
      addressLine2,
      city,
      state,
      pincode,
      country: country || "India",
      landmark,
      isDefault: makeDefault
    };

    user.addresses.push(newAddress);
    await user.save();

    const addedAddress = user.addresses[user.addresses.length - 1];

    res.status(201).json({ 
      success: true, 
      message: "Address added successfully",
      address: addedAddress 
    });
  } catch (err) {
    console.error("Error in addAddress:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ UPDATE ADDRESS ------------------
exports.updateAddress = async (req, res) => {
  try {
    const userId = req.user.id;
    const { addressId } = req.params;
    const { label, fullName, phone, addressLine1, addressLine2, city, state, pincode, country, landmark, isDefault } = req.body;

    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    const address = user.addresses.id(addressId);
    
    if (!address) {
      return res.status(404).json({ success: false, message: "Address not found" });
    }

    // If setting this as default, unset other defaults
    if (isDefault) {
      user.addresses.forEach(addr => {
        if (addr._id.toString() !== addressId) {
          addr.isDefault = false;
        }
      });
    }

    // Update fields
    if (label !== undefined) address.label = label;
    if (fullName !== undefined) address.fullName = fullName;
    if (phone !== undefined) address.phone = phone;
    if (addressLine1 !== undefined) address.addressLine1 = addressLine1;
    if (addressLine2 !== undefined) address.addressLine2 = addressLine2;
    if (city !== undefined) address.city = city;
    if (state !== undefined) address.state = state;
    if (pincode !== undefined) address.pincode = pincode;
    if (country !== undefined) address.country = country;
    if (landmark !== undefined) address.landmark = landmark;
    if (isDefault !== undefined) address.isDefault = isDefault;

    await user.save();

    res.json({ 
      success: true, 
      message: "Address updated successfully",
      address 
    });
  } catch (err) {
    console.error("Error in updateAddress:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ DELETE ADDRESS ------------------
exports.deleteAddress = async (req, res) => {
  try {
    const userId = req.user.id;
    const { addressId } = req.params;

    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    const address = user.addresses.id(addressId);
    
    if (!address) {
      return res.status(404).json({ success: false, message: "Address not found" });
    }

    const wasDefault = address.isDefault;
    
    // Remove the address
    address.deleteOne();

    // If deleted address was default and there are other addresses, set the first one as default
    if (wasDefault && user.addresses.length > 0) {
      user.addresses[0].isDefault = true;
    }

    await user.save();

    res.json({ 
      success: true, 
      message: "Address deleted successfully" 
    });
  } catch (err) {
    console.error("Error in deleteAddress:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ SET DEFAULT ADDRESS ------------------
exports.setDefaultAddress = async (req, res) => {
  try {
    const userId = req.user.id;
    const { addressId } = req.params;

    const user = await User.findById(userId);
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    const address = user.addresses.id(addressId);
    
    if (!address) {
      return res.status(404).json({ success: false, message: "Address not found" });
    }

    // Unset all defaults
    user.addresses.forEach(addr => {
      addr.isDefault = false;
    });

    // Set this as default
    address.isDefault = true;

    await user.save();

    res.json({ 
      success: true, 
      message: "Default address updated",
      address 
    });
  } catch (err) {
    console.error("Error in setDefaultAddress:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};

// ------------------ GET DEFAULT ADDRESS ------------------
exports.getDefaultAddress = async (req, res) => {
  try {
    const userId = req.user.id;

    const user = await User.findById(userId).select("addresses");
    
    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    const defaultAddress = user.addresses.find(addr => addr.isDefault);
    
    if (!defaultAddress) {
      return res.status(404).json({ 
        success: false, 
        message: "No default address set" 
      });
    }

    res.json({ success: true, address: defaultAddress });
  } catch (err) {
    console.error("Error in getDefaultAddress:", err);
    res.status(500).json({ success: false, message: "Internal server error" });
  }
};