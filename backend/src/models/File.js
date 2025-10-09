// backend/src/models/File.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

const FileSchema = new Schema({
  ownerId: { 
    type: Schema.Types.ObjectId, 
    ref: 'User', 
    index: true 
},
  storageKey: { 
    type: String, 
    required: true, 
    unique: true 
},
  cdnUrl: { 
    type: String 
},
  mimeType: { 
    type: String 
},
  size: Number,
  width: Number,
  height: Number
}, { timestamps: true });

module.exports = mongoose.model('File', FileSchema);
