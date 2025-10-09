const express = require("express");
const router = express.Router();
const likeController = require("../controllers/likeController");
const authMiddleware = require("../middlewares/authMiddleware");

// toggle like/unlike
router.post("/:artworkId", authMiddleware, likeController.likeArtwork);

// fetch all liked posts of logged-in user
router.get("/my-likes", authMiddleware, likeController.getLikedArtworks);

module.exports = router;