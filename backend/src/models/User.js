const mongoose = require('mongoose');
const { Schema } = mongoose;

const UserSchema = new Schema({
    email: { 
        type: String, 
        trim: true, 
        lowercase: true, 
        unique: true 
    },
    password:{
        type:String,
        required:true,
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
        }]
    }, { 
        timestamps: true 
    });

UserSchema.index({ name: 'text', bio: 'text' });

module.exports = mongoose.model('User', UserSchema);
