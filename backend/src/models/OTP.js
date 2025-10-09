// backend/src/models/OTP.js
const mongoose = require("mongoose");
const { Schema } = mongoose;

const OTPSchema = new Schema({
  email: { 
    type: String, 
    required: true, 
    index: true 
  },
  code: { 
    type: String, 
    required: true 
  },
  attempts: { 
    type: Number, 
    default: 0 
  },
  verified: { 
    type: Boolean, 
    default: false 
  },
  expiresAt: { 
    type: Date, 
    required: true, 
    index: { expireAfterSeconds: 0 } 
  }
}, { timestamps: true });

module.exports = mongoose.model("OTP", OTPSchema);
