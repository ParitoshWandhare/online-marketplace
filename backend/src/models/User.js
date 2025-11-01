// backend/src/models/User.js
const mongoose = require('mongoose');
const { Schema } = mongoose;

// Address schema for delivery
const AddressSchema = new Schema({
    label: { 
        type: String, 
        required: true,
        trim: true,
        enum: ['Home', 'Work', 'Other']
    },
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
    isDefault: {
        type: Boolean,
        default: false
    }
}, { timestamps: true });

const UserSchema = new Schema({
    email: { 
        type: String, 
        trim: true, 
        lowercase: true, 
        unique: true 
    },
    password: {
        type: String,
        required: true,
    },
    phone: { 
        type: String,  
        trim: true, 
        unique: true 
    },
    name: { 
        type: String, 
        required: true, 
        trim: true 
    },
    avatarUrl: { 
        type: String 
    },
    bio: { 
        type: String 
    },
    region: { 
        type: String 
    },
    lastSeen: { 
        type: Date 
    },
    likes: [{ 
        type: Schema.Types.ObjectId, 
        ref: "Artwork" 
    }],
    // Multiple delivery addresses
    addresses: {
        type: [AddressSchema],
        default: []
    }
}, { 
    timestamps: true 
});

UserSchema.index({ name: 'text', bio: 'text' });

module.exports = mongoose.model('User', UserSchema);