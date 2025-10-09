const bcrypt = require("bcrypt");
const User = require("../models/User");
const OTP = require("../models/OTP");
const otpGenerator = require("otp-generator");
const jwt = require("jsonwebtoken");
const mailSender = require("../utils/mailSender");
const { otpTemplate } = require("../mail/templates/emailVerificationTemplate");

require("dotenv").config();

// ------------------ SEND OTP ------------------
exports.sendOtp = async (req, res) => {
  try {
    const { email } = req.body;

    // Check if user already exists
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({
        success: false,
        message: "User already exists. Please login instead.",
      });
    }

    // Generate OTP
    let otp = otpGenerator.generate(6, {
      upperCase: false,
      specialChars: false,
      alphabets: false,
    });
    console.log("OTP Generated:", otp);

    // Ensure unique OTP
    let existingOtp = await OTP.findOne({ code: otp });
    while (existingOtp) {
      otp = otpGenerator.generate(6, {
        upperCase: false,
        specialChars: false,
        alphabets: false,
      });
      existingOtp = await OTP.findOne({ code: otp });
    }

    // Save OTP to DB
    const otpDoc = await OTP.create({
      email,
      code: otp,
      expiresAt: new Date(Date.now() + 5 * 60 * 1000), // 5 mins expiry
    });

    // Send email
    await mailSender(
    email,
    "Verify your Local Artisans Marketplace Account",
    otpTemplate(otp)
    );

    res.status(200).json({
      success: true,
      message: "OTP sent successfully",
      email,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      success: false,
      message: "Internal server error while sending OTP",
    });
  }
};

// ------------------ SIGNUP ------------------
exports.signup = async (req, res) => {
  try {
    const { name, email, password, confirmPassword, phone, otp } = req.body;

    if (!name || !email || !password || !confirmPassword || !otp) {
      return res.status(400).json({
        success: false,
        message: "All fields are required",
      });
    }

    if (password !== confirmPassword) {
      return res.status(400).json({
        success: false,
        message: "Passwords do not match",
      });
    }

    const existingUser = await User.findOne({ email });
    if (existingUser) {
      return res.status(400).json({
        success: false,
        message: "User already exists. Please login instead.",
      });
    }

    // Find the most recent OTP for this email
    const recentOtp = await OTP.findOne({ email }).sort({ createdAt: -1 });
    if (!recentOtp) {
      return res.status(400).json({
        success: false,
        message: "Please request OTP first",
      });
    }

    if (recentOtp.code !== otp) {
      return res.status(400).json({
        success: false,
        message: "Invalid OTP",
      });
    }

    if (recentOtp.expiresAt < new Date()) {
      return res.status(400).json({
        success: false,
        message: "OTP expired",
      });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const user = await User.create({
      name,
      email,
      password: hashedPassword,
      phone,
      avatarUrl: `https://api.dicebear.com/5.x/initials/svg?seed=${name}`,
    });

    res.status(201).json({
      success: true,
      message: "User registered successfully",
      user: {
        id: user._id,
        name: user.name,
        email: user.email,
        phone: user.phone,
      },
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      success: false,
      message: "Internal server error during signup",
    });
  }
};

// ------------------ LOGIN ------------------
exports.login = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        message: "Email and password are required",
      });
    }

    const user = await User.findOne({ email });
    if (!user) {
      return res.status(404).json({
        success: false,
        message: "User not found. Please signup first.",
      });
    }

    // Compare passwords
    const match = await bcrypt.compare(password, user.password);
    if (!match) {
      return res.status(401).json({
        success: false,
        message: "Invalid credentials",
      });
    }

    // Generate JWT
    const payload = { id: user._id, email: user.email, name: user.name };
    const token = jwt.sign(payload, process.env.JWT_SECRET, {
      expiresIn: "7d",
    });

    // Hide password in response
    user.password = undefined;

    res.status(200).json({
      success: true,
      message: "Login successful",
      token,
      user,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      success: false,
      message: "Internal server error during login",
    });
  }
};

// ------------------ GET PROFILE ------------------
exports.profile = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select("-password -__v");
    if (!user) {
      return res.status(404).json({
        success: false,
        message: "User not found",
      });
    }
    res.json({
      success: true,
      message: "User profile fetched successfully",
      user,
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({
      success: false,
      message: "Internal server error fetching profile",
    });
  }
};