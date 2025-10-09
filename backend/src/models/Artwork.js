// backend/src/models/Artwork.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

const MediaSchema = new Schema({
  url: { type: String, required: true },
  type: { type: String, enum: ['image', 'video'], default: 'image' },
  sizeBytes: Number,
  storageKey: String,
}, { _id: false });

const ArtworkSchema = new Schema({
  artistId: {
    type: Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true,
  },
  title: { type: String, required: true, trim: true },
  description: { type: String },
  media: { type: [MediaSchema], default: [] },
  price: { type: Number, required: true },
  currency: { type: String, default: 'INR' },
  quantity: { type: Number, default: 1 },
  status: {
    type: String,
    enum: ['draft', 'published', 'removed', 'out_of_stock'],
    default: 'draft',
  },
  likeCount: { type: Number, default: 0 },

  // New field for festive filtering - tags
  tags: {
    type: [String],
    default: [],
    index: true,
  },

  // Vector embeddings for semantic search (used by GenAI vector store)
  embedding: {
    type: [Number], // float vector from OpenAI embedding or similar
    index: "vector", // if using MongoDB Atlas Vector Search
    dimensions: 1536, // depends on embedding model used
  },

  // Meta tags for better intent matching
  festival_tags: { type: [String], default: [] },
  recipient_tags: { type: [String], default: [] },

}, { timestamps: true });

ArtworkSchema.index({ title: 'text', description: 'text', tags: 'text' });

module.exports = mongoose.model('Artwork', ArtworkSchema);