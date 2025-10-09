const nodemailer = require("nodemailer");
const sgTransport = require("nodemailer-sendgrid");

const mailSender = async (email, title, body) => {
  try {
    // Use SendGrid API transport (HTTPS, no SMTP)
    let transporter = nodemailer.createTransport(
      sgTransport({
        apiKey: process.env.SENDGRID_API_KEY,
      })
    );

    let info = await transporter.sendMail({
      from: `"Online MarketPlace" <${process.env.MAIL_USER}>`,
      to: email,
      subject: title,
      html: body,
    });

    console.log("Email sent:", info.messageId);
    return info;
  } catch (error) {
    console.error("Email send error:", error);
    throw error;
  }
};

module.exports = mailSender;
