// backend/src/controllers/likeController.js
const Like = require("../models/Like");
const Artwork = require("../models/Artwork");
const User = require("../models/User");

// ------------------ LIKE / UNLIKE ARTWORK ------------------
exports.likeArtwork = async (req, res) => {
  try {
    const { artworkId } = req.params;
    const userId = req.user.id;

    // check if already liked
    const existingLike = await Like.findOne({ userId, artworkId });

    if (existingLike) {
      // Unlike
      await existingLike.deleteOne();
      await Artwork.findByIdAndUpdate(artworkId, { $inc: { likeCount: -1 } });
      await User.findByIdAndUpdate(userId, { $pull: { likes: artworkId } });

      return res.json({
        success: true,
        message: "Artwork unliked",
      });
    } else {
      // Like
      await Like.create({ userId, artworkId });
      await Artwork.findByIdAndUpdate(artworkId, { $inc: { likeCount: 1 } });
      await User.findByIdAndUpdate(userId, { $addToSet: { likes: artworkId } });

      return res.json({
        success: true,
        message: "Artwork liked",
      });
    }
  } catch (err) {
    console.error("Error in likeArtwork:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while liking artwork",
    });
  }
};

// ------------------ GET USER'S LIKED ARTWORKS ------------------
exports.getLikedArtworks = async (req, res) => {
  try {
    const userId = req.user.id;
    
    const user = await User.findById(userId)
      .populate({
        path: "likes",
        populate: {
          path: "artistId",
          select: "name avatarUrl" // to get artist details
        }
      })
      .select("likes");

    if (!user) {
      return res.status(404).json({ success: false, message: "User not found" });
    }

    res.json({
      success: true,
      count: user.likes.length,
      artworks: user.likes,
    });
  } catch (err) {
    console.error("Error in getLikedArtworks:", err);
    res.status(500).json({
      success: false,
      message: "Internal server error while fetching liked artworks",
    });
  }
};
