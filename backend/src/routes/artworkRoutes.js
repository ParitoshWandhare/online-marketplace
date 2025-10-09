const express = require("express");
const router = express.Router();
const artworkController = require("../controllers/artworkController");
const authMiddleware = require("../middlewares/authMiddleware");
const upload = require("../middlewares/upload");

// create artwork with file upload
router.post(
  "/",
  authMiddleware,
  upload.array("media", 5), // up to 5 files
  artworkController.createArtwork
);

// fetch all artworks
router.get("/", authMiddleware, artworkController.getAllArtworks);

// fetch one artwork
router.get("/:id", authMiddleware, artworkController.getArtworkById);

// delete artwork
router.delete("/:id", authMiddleware, artworkController.deleteArtwork);

// my artworks
router.get("/me/my-artworks", authMiddleware, artworkController.myArtworks);

// edit artwork
router.put("/:id", authMiddleware, artworkController.updateArtwork);

// Restock artwork (seller only)
router.patch("/:id/restock", authMiddleware, artworkController.restockArtwork);

module.exports = router;
