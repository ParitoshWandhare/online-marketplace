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
    },
    titleCopy: String,
    qty: { 
        type: Number, 
        default: 1, 
        min: 1 
    },
    unitPrice: Number,
    currency: { 
        type: String, 
        default: "INR" 
    },
  },
  { _id: false }
);

// Address schema for delivery
const AddressSchema = new Schema(
  {
    fullName: { 
        type: String, 
        required: true,
        trim: true 
    },
    phone: { 
        type: String, 
        required: true,
        trim: true 
    },
    addressLine1: { 
        type: String, 
        required: true,
        trim: true 
    },
    addressLine2: { 
        type: String,
        trim: true 
    },
    city: { 
        type: String, 
        required: true,
        trim: true 
    },
    state: { 
        type: String, 
        required: true,
        trim: true 
    },
    pincode: { 
        type: String, 
        required: true,
        trim: true 
    },
    country: { 
        type: String, 
        default: "India",
        trim: true 
    },
    landmark: { 
        type: String,
        trim: true 
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
    },
    total: { 
        type: Number, 
        required: true 
    },
    currency: { 
        type: String, 
        default: "INR" 
    },

    // Delivery address
    shippingAddress: {
        type: AddressSchema,
        required: true
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

    // Optional: Track shipment
    trackingNumber: String,
    shippedAt: Date,
    deliveredAt: Date,
  },
  { timestamps: true }
);

OrderSchema.index({ buyerId: 1 });
OrderSchema.index({ "items.sellerId": 1 });

module.exports = mongoose.model("Order", OrderSchema);