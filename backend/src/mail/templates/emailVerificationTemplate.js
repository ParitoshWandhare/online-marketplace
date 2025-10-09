exports.otpTemplate = (otp) => {
  return `
  <body style="font-family: Arial, sans-serif; background-color: #f9fafb; margin: 0; padding: 0;">
    <div style="max-width: 600px; margin: auto; background: #ffffff; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); overflow: hidden;">
      
      <!-- Header -->
      <div style="background: #2d6a4f; padding: 16px; text-align: center;">
        <a href="https://orchid-marketplace.vercel.app/" target="_blank">
          <img src="https://i.ibb.co/4pFg4Jm/marketplace-logo.png" alt="Marketplace Logo" style="height: 50px;">
        </a>
      </div>

      <!-- Body -->
      <div style="padding: 24px; color: #333333; font-size: 15px; line-height: 1.6;">
        <h2 style="margin-top: 0; color: #1b4332;">OTP Verification</h2>
        <p>Dear User,</p>
        <p>Welcome to <b>ORCHID - Local Artisans Marketplace</b>! To complete your registration, please use the following One-Time Password (OTP):</p>
        
        <div style="text-align: center; margin: 30px 0;">
          <span style="display: inline-block; font-size: 28px; font-weight: bold; background: #d8f3dc; color: #1b4332; padding: 12px 24px; border-radius: 6px; letter-spacing: 4px;">
            ${otp}
          </span>
        </div>

        <p>This OTP is valid for <b>5 minutes</b>. If you did not request this verification, please ignore this email.</p>
        <p>Once verified, you’ll be able to explore unique handmade products and support local artisans directly.</p>
      </div>

      <!-- Footer -->
      <div style="background: #f1f3f5; padding: 16px; text-align: center; font-size: 13px; color: #666;">
        <p>If you have any questions, feel free to contact us at 
          <a href="mailto:support@localartisans.com" style="color: #2d6a4f; text-decoration: none;">support@localartisans.com</a>.
        </p>
        <p>&copy; ${new Date().getFullYear()} ORCHID. All rights reserved.</p>
      </div>

    </div>
  </body>
  `;
};
