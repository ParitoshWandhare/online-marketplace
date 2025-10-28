// backend/src/controllers/artworkController.js
const Artwork = require("../models/Artwork");
const mongoose = require("mongoose");
const { cloudinary } = require("../config/cloudinary");
const giftAIService = require("../services/giftAIService");

// ------------------ CREATE ARTWORK ------------------
exports.createArtwork = async (req, res) => {
  try {
    const { title, description, price, currency, quantity, status, tags } = req.body;

    if (!title || !price) {
      return res.status(400).json({
        success: false,
        message: "Title and price are required",
      });
    }

    let media = (req.files || []).map((file) => ({
      url: file.path,
      type: file.mimetype.startsWith("video") ? "video" : "image",
      sizeBytes: file.size,
      storageKey: file.filename,
    }));

    const artwork = await Artwork.create({
      artistId: req.user.id,
      title,
      description,
      price,
      currency: currency || "INR",
      quantity: quantity || 1,
      status: status || "draft",
      tags: tags || [],
      media,
    });

    // 🎁 AUTO-INDEX: Index artwork in AI vector store if published
    if (artwork.status === "published") {
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`✅ Artwork ${artwork._id} indexed in AI vector store`);
      } catch (error) {
        console.error(`⚠️ Failed to index artwork ${artwork._id}:`, error.message);
        // Don't fail the request if indexing fails
      }
    }

    res.status(201).json({
      success: true,
      message: "Artwork posted successfully",
      artwork,
    });
  } catch (err) {
    console.error("Error creating artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while creating artwork",
      error: err.message,
    });
  }
};

// ------------------ UPDATE ARTWORK ------------------
exports.updateArtwork = async (req, res) => {
  try {
    const { id } = req.params;
    const { title, description, price, currency, quantity, status, tags } = req.body;

    const artwork = await Artwork.findById(id);
    if (!artwork) {
      return res.status(404).json({ 
        success: false, 
        message: "Artwork not found" 
      });
    }

    if (artwork.artistId.toString() !== req.user.id) {
      return res.status(403).json({ 
        success: false, 
        message: "Unauthorized" 
      });
    }

    if (artwork.status !== "draft") {
      return res.status(400).json({
        success: false,
        message: "Only artworks in draft state can be edited",
      });
    }

    // Update fields
    if (title) artwork.title = title;
    if (description) artwork.description = description;
    if (price) artwork.price = price;
    if (currency) artwork.currency = currency;
    if (quantity) artwork.quantity = quantity;
    if (tags) artwork.tags = tags;
    
    // Track status change
    const wasPublished = artwork.status === "published";
    if (status) artwork.status = status;
    const isNowPublished = artwork.status === "published";

    await artwork.save();

    // 🎁 AUTO-INDEX: Index if newly published or re-index if already published
    if (isNowPublished && !wasPublished) {
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`✅ Artwork ${artwork._id} indexed in AI vector store`);
      } catch (error) {
        console.error(`⚠️ Failed to index artwork ${artwork._id}:`, error.message);
      }
    } else if (isNowPublished && wasPublished) {
      // Re-index if already published (content changed)
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`♻️ Artwork ${artwork._id} re-indexed in AI vector store`);
      } catch (error) {
        console.error(`⚠️ Failed to re-index artwork ${artwork._id}:`, error.message);
      }
    }

    res.json({
      success: true,
      message: "Artwork updated successfully",
      artwork,
    });
  } catch (err) {
    console.error("Error updating artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while updating artwork",
      error: err.message,
    });
  }
};

// ------------------ GET ALL ARTWORKS ------------------
exports.getAllArtworks = async (req, res) => {
  try {
    const artworks = await Artwork.find({ status: "published" })
      .populate("artistId", "name email avatarUrl")
      .sort({ createdAt: -1 });

    res.json({
      success: true,
      count: artworks.length,
      artworks,
    });
  } catch (err) {
    console.error("Error fetching artworks:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching artworks",
    });
  }
};

// ------------------ GET ARTWORK BY ID ------------------
exports.getArtworkById = async (req, res) => {
  try {
    const { id } = req.params;

    if (!mongoose.Types.ObjectId.isValid(id)) {
      return res.status(400).json({ success: false, message: "Invalid ID" });
    }

    const artwork = await Artwork.findById(id).populate(
      "artistId",
      "name email avatarUrl"
    );

    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    res.json({
      success: true,
      artwork,
    });
  } catch (err) {
    console.error("Error fetching artwork by ID:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching artwork",
    });
  }
};

// ------------------ DELETE ARTWORK ------------------
exports.deleteArtwork = async (req, res) => {
  try {
    const { id } = req.params;

    const artwork = await Artwork.findById(id);

    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    if (artwork.artistId.toString() !== req.user.id) {
      return res.status(403).json({ success: false, message: "Unauthorized" });
    }

    await artwork.deleteOne();

    // Note: Vector store cleanup would require additional API endpoint
    // For now, deleted items will simply not be returned in searches

    res.json({
      success: true,
      message: "Artwork deleted successfully",
    });
  } catch (err) {
    console.error("Error deleting artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while deleting artwork",
    });
  }
};

// ------------------ GET USER'S ARTWORKS ------------------
exports.myArtworks = async (req, res) => {
  try {
    const artworks = await Artwork.find({ artistId: req.user.id }).sort({
      createdAt: -1,
    });

    res.json({
      success: true,
      count: artworks.length,
      artworks,
    });
  } catch (err) {
    console.error("Error fetching user's artworks:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching user's artworks",
    });
  }
};

// ------------------ RESTOCK ARTWORK ------------------
exports.restockArtwork = async (req, res) => {
  try {
    const { id } = req.params;
    const { quantity } = req.body;

    if (!quantity || quantity <= 0) {
      return res.status(400).json({
        success: false,
        message: "Quantity must be greater than 0",
      });
    }

    const artwork = await Artwork.findById(id);

    if (!artwork) {
      return res.status(404).json({ success: false, message: "Artwork not found" });
    }

    if (artwork.artistId.toString() !== req.user.id) {
      return res.status(403).json({ success: false, message: "Unauthorized" });
    }

    artwork.quantity += Number(quantity);

    if (artwork.status === "out_of_stock" || artwork.status === "removed") {
      artwork.status = "published";
      
      // 🎁 AUTO-INDEX: Re-index when restocking
      try {
        await giftAIService.indexArtwork(artwork);
        console.log(`♻️ Artwork ${artwork._id} re-indexed after restocking`);
      } catch (error) {
        console.error(`⚠️ Failed to re-index artwork ${artwork._id}:`, error.message);
      }
    }

    await artwork.save();

    res.json({
      success: true,
      message: "Artwork restocked successfully",
      artwork,
    });
  } catch (err) {
    console.error("Error restocking artwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while restocking artwork",
      error: err.message,
    });
  }
};