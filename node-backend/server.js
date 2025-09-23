require("dotenv").config();
const express = require("express");
const bodyParser = require("body-parser");
const Razorpay = require("razorpay");
const crypto = require("crypto");
const cors = require("cors");
const multer = require("multer"); // Now this works after installation
const fs = require("fs");

const app = express();
const port = 3000;

app.use(cors());
app.use(bodyParser.json());

// Ensure uploads directory exists
if (!fs.existsSync("./uploads")) {
  fs.mkdirSync("./uploads");
}

// -------------------- Razorpay Setup --------------------
const razorpay = new Razorpay({
  key_id: process.env.RAZORPAY_KEY_ID,
  key_secret: process.env.RAZORPAY_KEY_SECRET,
});

// -------------------- Multer Setup (for future use) --------------------
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, "./uploads"),
  filename: (req, file, cb) => cb(null, Date.now() + "-" + file.originalname),
});
const upload = multer({ storage });

// -------------------- Health Check --------------------
app.get("/", (_, res) => {
  res.send("✅ Razorpay backend is running");
});

// -------------------- Razorpay Routes --------------------
app.post("/create-order", async (req, res) => {
  try {
    const { amount } = req.body;
    const order = await razorpay.orders.create({
      amount,
      currency: "INR",
      receipt: "receipt#1",
      payment_capture: 1,
    });
    res.json(order);
  } catch (err) {
    console.error("Razorpay order error:", err);
    res.status(500).json({ error: err.message });
  }
});

app.post("/verify-payment", (req, res) => {
  const { razorpay_order_id, razorpay_payment_id, razorpay_signature } = req.body;
  const hmac = crypto
    .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET)
    .update(`${razorpay_order_id}|${razorpay_payment_id}`)
    .digest("hex");

  if (hmac === razorpay_signature) {
    res.json({ success: true });
  } else {
    res.json({ success: false, message: "Invalid signature" });
  }
});

// -------------------- Start Server --------------------
app.listen(port, () => {
  console.log(`🚀 Server running at http://localhost:${port}`);
});
