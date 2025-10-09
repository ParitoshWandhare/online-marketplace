const multer = require("multer");
const { CloudinaryStorage } = require("multer-storage-cloudinary");
const { cloudinary } = require("../config/cloudinary");

const storage = new CloudinaryStorage({
  cloudinary,
  params: async (req, file) => {
    let folder = "artworks";
    let resource_type = "image";

    if (file.mimetype.startsWith("video")) {
      resource_type = "video";
    }

    return {
      folder,
      resource_type,
      public_id: `${Date.now()}-${file.originalname.split(".")[0]}`,
    };
  },
});

const upload = multer({ storage });

module.exports = upload;
