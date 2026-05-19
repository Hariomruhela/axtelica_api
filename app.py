from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import os
import io
import random
import base64
import smtplib
import hmac
import hashlib
import time

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

EMAIL_USER  = os.getenv("EMAIL_USER")
EMAIL_PASS  = os.getenv("EMAIL_PASS")

# ✅ Keep this secret & consistent across deployments — set it in Vercel env vars
CAPTCHA_SECRET = os.getenv("CAPTCHA_SECRET", "axtelica-captcha-secret-2025")

# =========================
# FLASK APP  (no session needed)
# =========================
app = Flask(__name__)

# ✅ Allowed origins — add all your frontend URLs here
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://axtelica.com",
    "https://www.axtelica.com",
]

CORS(app, origins=ALLOWED_ORIGINS, supports_credentials=True)

# =========================
# CAPTCHA TOKEN HELPERS
# =========================
CAPTCHA_TTL = 600  # seconds — token valid for 10 minutes

def make_captcha_token(answer: str) -> str:
    """
    Build a stateless signed token:  base64(answer:timestamp):hmac_signature
    The answer is stored inside the token itself, protected by an HMAC.
    No session or database needed.
    """
    ts      = str(int(time.time()))
    payload = base64.urlsafe_b64encode(f"{answer.upper()}:{ts}".encode()).decode()
    sig     = hmac.new(CAPTCHA_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_captcha_token(token: str, user_answer: str) -> tuple[bool, str]:
    """
    Verify the token.
    Returns (True, "") on success, or (False, error_message) on failure.
    """
    try:
        payload, sig = token.rsplit(".", 1)
    except ValueError:
        return False, "Invalid CAPTCHA token format."

    # Check signature
    expected_sig = hmac.new(CAPTCHA_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_sig, sig):
        return False, "Invalid CAPTCHA token. Please refresh and try again."

    # Decode payload
    try:
        decoded        = base64.urlsafe_b64decode(payload.encode()).decode()
        answer, ts_str = decoded.rsplit(":", 1)
        ts             = int(ts_str)
    except Exception:
        return False, "Corrupted CAPTCHA token. Please refresh and try again."

    # Check expiry
    if time.time() - ts > CAPTCHA_TTL:
        return False, "CAPTCHA expired. Please refresh the code and try again."

    # Check answer (case-insensitive)
    if user_answer.strip().upper() != answer.upper():
        return False, "Incorrect CAPTCHA code. Please try again."

    return True, ""


# =========================
# GENERATE CAPTCHA TEXT
# =========================
def generate_captcha_text(length=5):
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "".join(random.choices(chars, k=length))


# =========================
# GENERATE CAPTCHA IMAGE
# =========================
def generate_captcha_image(text):
    width, height = 180, 60
    image = Image.new("RGB", (width, height), color=(245, 245, 250))
    draw  = ImageDraw.Draw(image)

    # Noise lines
    for _ in range(6):
        draw.line(
            [(random.randint(0, width), random.randint(0, height)),
             (random.randint(0, width), random.randint(0, height))],
            fill=(random.randint(150, 220), random.randint(150, 220), random.randint(150, 220)),
            width=1
        )

    # Noise dots
    for _ in range(80):
        draw.point(
            (random.randint(0, width), random.randint(0, height)),
            fill=(random.randint(100, 200), random.randint(100, 200), random.randint(100, 200))
        )

    # Font
    font = None
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        try:
            font = ImageFont.truetype(path, 42)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    # Draw characters
    x_offset = 12
    for char in text:
        color    = (random.randint(20, 100), random.randint(20, 100), random.randint(20, 100))
        y_offset = random.randint(5, 18)
        draw.text((x_offset, y_offset), char, font=font, fill=color)
        x_offset += random.randint(28, 34)

    image = image.filter(ImageFilter.GaussianBlur(radius=0.8))

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")


# =========================
# SEND EMAIL
# =========================
def send_email(subject, html_content, reply_to=None):
    try:
        msg           = MIMEMultipart()
        msg["From"]   = "Axtelica <info@axtelica.com>"
        msg["To"]     = "hello@techquitoes.com"  
        msg["Subject"] = subject
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(EMAIL_USER, "hello@techquitoes.com", msg.as_string())
        server.quit()
        print("✅ Email sent")
    except Exception as e:
        print("❌ Email error:", e)
        raise e


# =========================
# ROUTES
# =========================

@app.route("/", methods=["GET"])
def home():
    return jsonify({"success": True, "message": "API Running 🚀"})


# ── CAPTCHA GENERATE ──────────────────────────────────────────
@app.route("/api/captcha", methods=["GET"])
def get_captcha():
    """
    Returns:
      captcha_image  — base64 PNG
      captcha_token  — signed token containing the answer (sent to frontend,
                       returned with the form, verified on the server)
    """
    try:
        text  = generate_captcha_text()
        token = make_captcha_token(text)
        image = generate_captcha_image(text)
        print(f"✅ CAPTCHA generated (stateless token)")
        return jsonify({"success": True, "captcha_image": image, "captcha_token": token})
    except Exception as e:
        print("❌ CAPTCHA error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── DEMO FORM ─────────────────────────────────────────────────
@app.route("/api/demo", methods=["POST"])
def demo():
    try:
        data = request.get_json()
        print("✅ DEMO data received")

        # ── CAPTCHA VERIFICATION ──
        user_answer   = data.get("captchaAnswer", "")
        captcha_token = data.get("captchaToken", "")

        if not user_answer:
            return jsonify({"success": False, "error": "Please enter the CAPTCHA code."}), 400
        if not captcha_token:
            return jsonify({"success": False, "error": "CAPTCHA token missing. Please refresh the page."}), 400

        ok, err_msg = verify_captcha_token(captcha_token, user_answer)
        if not ok:
            return jsonify({"success": False, "error": err_msg}), 400
        # ── END CAPTCHA ──

        firstName       = data.get("firstName")
        lastName        = data.get("lastName")
        company         = data.get("company")
        email           = data.get("email")
        phone           = data.get("phone")
        employees       = data.get("employees")
        country         = data.get("country")
        scheduleDemoFor = data.get("scheduleDemoFor")

        html = f"""
        <h2>📩 New Demo Request from Axtelica website</h2>
        <p><b>Name:</b> {firstName} {lastName}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Company:</b> {company}</p>
        <p><b>Phone:</b> {phone}</p>
        <p><b>Employees:</b> {employees}</p>
        <p><b>Country:</b> {country}</p>
        <p><b>Schedule Demo For:</b> {scheduleDemoFor}</p>
        <hr style="margin:20px 0;" />
        <p style="font-size:12px;color:gray;">Submitted from Axtelica Demo Form</p>
        """

        send_email("📩 New Demo Request from Axtelica", html, email)
        return jsonify({"success": True})

    except Exception as e:
        print("❌ DEMO error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── CONTACT ───────────────────────────────────────────────────
@app.route("/api/contact", methods=["POST"])
def contact():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data received"}), 400

        email      = data.get("email",      "").strip()
        firstName  = data.get("firstName",  "").strip()
        lastName   = data.get("lastName",   "").strip()
        company    = data.get("company",    "").strip()
        phone      = data.get("phone",      "").strip()
        department = data.get("department", "").strip()
        message    = data.get("message",    "").strip()

        for field, label in [
            (firstName, "First Name"), (lastName, "Last Name"), (email, "Email"),
            (company, "Company"), (phone, "Phone"), (department, "Department"),
            (message, "Message"),
        ]:
            if not field:
                return jsonify({"success": False, "error": f"{label} is required"}), 400

        html = f"""
        <div style="max-width:600px;margin:auto;font-family:Arial;padding:20px;
                    border:1px solid #eee;border-radius:10px;">
            <h2 style="color:#FF3366;">📩 New Contact Message from Axtelica</h2>
            <p><b>Name:</b> {firstName} {lastName}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Company:</b> {company}</p>
            <p><b>Phone:</b> {phone}</p>
            <p><b>Department:</b> {department}</p>
            <hr style="margin:20px 0;" />
            <p><b>Message:</b></p><p>{message}</p>
            <hr style="margin:20px 0;" />
            <p style="font-size:12px;color:gray;">Submitted from Axtelica Contact Form</p>
        </div>
        """
        send_email("📩 New Contact Message", html, email)
        return jsonify({"success": True, "message": "Contact message sent successfully"})

    except Exception as e:
        print("❌ CONTACT error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ── PRODUCT DEMO ──────────────────────────────────────────────
@app.route("/api/product", methods=["POST"])
def product():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No JSON data received"}), 400

        firstName = data.get("firstName", "").strip()
        lastName  = data.get("lastName",  "").strip()
        company   = data.get("company",   "").strip()
        email     = data.get("email",     "").strip()
        phone     = data.get("phone",     "").strip()
        employees = data.get("employees", "").strip()
        country   = data.get("country",   "").strip()

        for field, label in [
            (firstName, "First Name"), (lastName, "Last Name"), (company, "Company"),
            (email, "Email"), (phone, "Phone"), (employees, "Employees"), (country, "Country"),
        ]:
            if not field:
                return jsonify({"success": False, "error": f"{label} is required"}), 400

        html = f"""
        <div style="max-width:600px;margin:auto;font-family:Arial;padding:20px;
                    border:1px solid #eee;border-radius:10px;">
            <h2 style="color:#FF3366;">📩 New Demo Request From Axtelica Product</h2>
            <p><b>Name:</b> {firstName} {lastName}</p>
            <p><b>Company:</b> {company}</p>
            <p><b>Email:</b> {email}</p>
            <p><b>Phone:</b> {phone}</p>
            <p><b>Employees:</b> {employees}</p>
            <p><b>Country:</b> {country}</p>
            <hr style="margin:20px 0;" />
            <p style="font-size:12px;color:gray;">Submitted from Axtelica Demo Form</p>
        </div>
        """
        send_email("📩 New Demo Request from Axtelica Product", html, email)
        return jsonify({"success": True, "message": "Demo request sent successfully"})

    except Exception as e:
        print("❌ PRODUCT error:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)