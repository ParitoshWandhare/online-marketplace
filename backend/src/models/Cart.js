// backend/src/models/Cart.js
const mongoose = require("mongoose");
const { Schema } = mongoose;

const CartItemSchema = new Schema({
  artworkId: { 
    type: Schema.Types.ObjectId, 
    ref: "Artwork", 
    required: true },
  qty: { 
    type: Number, 
    default: 1,
    min: 1
  },
}, { _id: false });

const CartSchema = new Schema({
  userId: { 
    type: Schema.Types.ObjectId, 
    ref: "User", 
    required: true, 
    unique: true },
  items: { 
    type: [CartItemSchema], 
    default: [] 
},
}, { timestamps: true });

module.exports = mongoose.model("Cart", CartSchema);
