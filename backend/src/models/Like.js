// backend/src/models/Like.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

const LikeSchema = new Schema({
    userId: { 
        type: Schema.Types.ObjectId, 
        ref: 'User', 
        required: true 
    },
    artworkId: { 
        type: Schema.Types.ObjectId, 
        ref: 'Artwork', 
        required: true 
    }
}, { timestamps: true });

// Ensure one like per user per artwork
LikeSchema.index({ userId: 1, artworkId: 1 }, { unique: true });

module.exports = mongoose.model('Like', LikeSchema);
