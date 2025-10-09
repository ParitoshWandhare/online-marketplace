// backend/src/models/Order.js
const mongoose = require("mongoose");
const { Schema } = mongoose;

const OrderItemSchema = new Schema(
  {
    artworkId: { 
        type: Schema.Types.ObjectId, 
        ref: "Artwork", 
        required: true 
    },
    sellerId: { 
        type: Schema.Types.ObjectId, 
        ref: "User", 
        required: true 
    }, // seller tied to each item
    titleCopy: String,   // snapshot of title
    qty: { 
        type: Number, 
        default: 1, 
        min: 1 
    },
    unitPrice: Number,   // snapshot of price
    currency: { 
        type: String, 
        default: "INR" 
    },
  },
  { _id: false }
);

const OrderSchema = new Schema(
  {
    buyerId: { 
        type: Schema.Types.ObjectId, 
        ref: "User", 
        required: true 
    },
    items: {
        type: [OrderItemSchema], 
        default: [] 
    }, // each item has its seller
    total: { 
        type: Number, 
        required: true 
    },
    currency: { 
        type: String, 
        default: "INR" 
    },

    // Razorpay payment info
    razorpayOrderId: String,
    razorpayPaymentId: String,
    razorpaySignature: String,

    status: {
      type: String,
      enum: [
        "created",
        "pending",
        "paid",
        "failed",
        "shipped",
        "out_for_delivery",
        "delivered",
        "cancelled",
      ],
      default: "created",
    },
  },
  { timestamps: true }
);

OrderSchema.index({ buyerId: 1 });
OrderSchema.index({ "items.sellerId": 1 }); // since sellerId is nested now

module.exports = mongoose.model("Order", OrderSchema);
