// backend/src/models/Story.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

const StorySchema = new Schema({
    artworkId: { 
        type: Schema.Types.ObjectId, 
        ref: 'Artwork', 
        required: true, 
        index: true },
    lang: { 
        type: String, 
        default: 'en' 
    },
    title: { 
        type: String 
    },
    narrative: { 
        type: String 
    },
    ttsUrl: { 
        type: String 
    }, // optional: audio file
    approvedByArtist: { 
        type: Boolean, 
        default: false 
    }
}, { timestamps: true });

StorySchema.index({ artworkId: 1, lang: 1 }, { unique: true });

module.exports = mongoose.model('Story', StorySchema);
