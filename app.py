from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import os
import io
import random
import base64
import hmac
import hashlib
import time
import requests as http_requests

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# =========================================================
# LOAD ENV VARIABLES
# =========================================================
load_dotenv()

MS_TENANT_ID = os.getenv("MS_TENANT_ID")
MS_CLIENT_ID = os.getenv("MS_CLIENT_ID")
MS_CLIENT_SECRET = os.getenv("MS_CLIENT_SECRET")
MS_SENDER_EMAIL = os.getenv("MS_SENDER_EMAIL")
SALES_TO_EMAIL = os.getenv("SALES_TO_EMAIL")

CAPTCHA_SECRET = os.getenv(
    "CAPTCHA_SECRET",
    "axtelica-captcha-secret-2025"
)

# =========================================================
# FLASK APP
# =========================================================
app = Flask(__name__)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://axtelica.com",
    "https://www.axtelica.com",
]

CORS(
    app,
    origins=ALLOWED_ORIGINS,
    supports_credentials=True
)

# =========================================================
# MICROSOFT GRAPH ACCESS TOKEN
# =========================================================
def get_ms_access_token():

    url = f"https://login.microsoftonline.com/{MS_TENANT_ID}/oauth2/v2.0/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": MS_CLIENT_ID,
        "client_secret": MS_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = http_requests.post(
        url,
        data=payload,
        timeout=20
    )

    response.raise_for_status()

    return response.json()["access_token"]


# =========================================================
# SEND EMAIL USING MICROSOFT GRAPH
# =========================================================
def send_email(
    to_email,
    subject,
    html_content,
    reply_to=None
):

    try:

        access_token = get_ms_access_token()

        message = {
            "subject": subject,

            "body": {
                "contentType": "HTML",
                "content": html_content
            },

            "from": {
                "emailAddress": {
                    "address": MS_SENDER_EMAIL,
                    "name": "Axtelica"
                }
            },

            "toRecipients": [
                {
                    "emailAddress": {
                        "address": to_email
                    }
                }
            ]
        }

        # reply-to
        if reply_to:
            message["replyTo"] = [
                {
                    "emailAddress": {
                        "address": reply_to
                    }
                }
            ]

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        graph_url = (
            f"https://graph.microsoft.com/v1.0/users/"
            f"{MS_SENDER_EMAIL}/sendMail"
        )

        response = http_requests.post(
            graph_url,
            headers=headers,
            json={
                "message": message,
                "saveToSentItems": True
            },
            timeout=20
        )

        if response.status_code == 202:
            print("✅ Email sent successfully")
            return True

        print("❌ Graph API Error")
        print(response.status_code)
        print(response.text)

        return False

    except Exception as e:
        print("❌ EMAIL ERROR:", str(e))
        return False


# =========================================================
# INTERNAL SALES EMAIL TEMPLATE
# =========================================================
def internal_email_template(
    title,
    name,
    company,
    email,
    phone,
    extra_fields="",
    message=""
):

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background-color:#f4f4f4;padding:20px;">

      <tr>
        <td align="center">

          <table width="600" cellpadding="0" cellspacing="0"
          border="0"
          style="background:#ffffff;
          border-radius:8px;
          overflow:hidden;
          border:1px solid #ddd;">

            <tr>
              <td style="padding:20px;
              background:linear-gradient(90deg,#2563eb,#9333ea);
              color:#ffffff;
              text-align:center;">

                <h2 style="margin:0;">
                  {title}
                </h2>

              </td>
            </tr>

            <tr>
              <td style="padding:30px;">

                <p style="font-family:Arial;
                color:#333;">

                You received a new inquiry from the website.

                </p>

                <table width="100%"
                cellpadding="10"
                cellspacing="0"
                border="0"
                style="border:1px solid #eee;
                margin-top:20px;">

                  <tr>
                    <td width="30%"
                    style="font-weight:bold;color:#555;">
                    Name:
                    </td>

                    <td style="color:#333;">
                    {name}
                    </td>
                  </tr>

                  <tr style="background-color:#f9f9f9;">
                    <td style="font-weight:bold;color:#555;">
                    Company:
                    </td>

                    <td style="color:#333;">
                    {company}
                    </td>
                  </tr>

                  <tr>
                    <td style="font-weight:bold;color:#555;">
                    Email:
                    </td>

                    <td style="color:#2563eb;">
                    {email}
                    </td>
                  </tr>

                  <tr style="background-color:#f9f9f9;">
                    <td style="font-weight:bold;color:#555;">
                    Phone:
                    </td>

                    <td style="color:#333;">
                    {phone}
                    </td>
                  </tr>

                  {extra_fields}

                </table>

                {message}

              </td>
            </tr>

            <tr>
              <td style="padding:20px;
              text-align:center;
              font-size:12px;
              color:#888;
              background-color:#f9f9f9;">

              © 2026 Axtelica. All rights reserved.

              </td>
            </tr>

          </table>

        </td>
      </tr>

    </table>
    """


# =========================================================
# CUSTOMER AUTO RESPONSE TEMPLATE
# =========================================================
def customer_auto_response(name):

    return f"""
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
    style="background-color:#f4f4f4;padding:20px;">

      <tr>
        <td align="center">

          <table width="600"
          cellpadding="0"
          cellspacing="0"
          border="0"
          style="background:#ffffff;
          border-radius:8px;
          overflow:hidden;
          border:1px solid #ddd;">

            <tr>
              <td style="padding:30px;
              background:linear-gradient(90deg,#2563eb,#9333ea);
              background:#4f46e5;
                              
              color:#ffffff;
              text-align:center;">

                <h1 style="margin:0;font-size:24px;">
                  Thanks for reaching out!
                </h1>

              </td>
            </tr>

            <tr>
              <td style="padding:30px;
              font-family:Arial,sans-serif;
              color:#333;">

                <p>Hi {name},</p>

                <p>
                  Thank you for contacting Axtelica.
                  We have received your request and
                  our team is reviewing it.
                </p>

                <p>
                  A member of our team will contact you
                  within <b>24 business hours</b>.
                </p>

                <p style="margin-top:30px;">

                  Explore our solutions:
                  <a href="https://axtelica.com"
                  style="color:#2563eb;
                  font-weight:bold;">

                  Visit Website

                  </a>

                </p>

                <p>
                  Best Regards,<br>
                  The Axtelica Team
                </p>

              </td>
            </tr>

            <tr>
              <td style="padding:20px;
              text-align:center;
              font-size:12px;
              color:#888;
              background-color:#f9f9f9;">

                Axtelica |
                www.axtelica.com

              </td>
            </tr>

          </table>

        </td>
      </tr>

    </table>
    """


# =========================================================
# CAPTCHA SETTINGS
# =========================================================
CAPTCHA_TTL = 600


# =========================================================
# GENERATE CAPTCHA TEXT
# =========================================================
def generate_captcha_text(length=5):

    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    return "".join(random.choices(chars, k=length))


# =========================================================
# CREATE CAPTCHA TOKEN
# =========================================================
def make_captcha_token(answer):

    timestamp = str(int(time.time()))

    payload_string = f"{answer.upper()}:{timestamp}"

    payload = base64.urlsafe_b64encode(
        payload_string.encode()
    ).decode()

    signature = hmac.new(
        CAPTCHA_SECRET.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{payload}.{signature}"


# =========================================================
# VERIFY CAPTCHA TOKEN
# =========================================================
def verify_captcha_token(token, user_answer):

    try:

        if not token:
            return False, "CAPTCHA token missing"

        if not user_answer:
            return False, "Please enter CAPTCHA"

        payload, signature = token.rsplit(".", 1)

        expected_signature = hmac.new(
            CAPTCHA_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            signature,
            expected_signature
        ):
            return False, "Invalid CAPTCHA token"

        padded_payload = payload + "=" * (-len(payload) % 4)

        decoded = base64.urlsafe_b64decode(
            padded_payload.encode()
        ).decode()

        answer, timestamp = decoded.rsplit(":", 1)

        timestamp = int(timestamp)

        if time.time() - timestamp > CAPTCHA_TTL:
            return False, "CAPTCHA expired"

        if user_answer.strip().upper() != answer.strip().upper():
            return False, "Incorrect CAPTCHA code"

        return True, ""

    except Exception as e:
        print("❌ CAPTCHA VERIFY ERROR:", str(e))
        return False, "CAPTCHA verification failed"


# =========================================================
# GENERATE CAPTCHA IMAGE
# =========================================================
def generate_captcha_image(text):

    width = 180
    height = 60

    image = Image.new(
        "RGB",
        (width, height),
        color=(245, 245, 250)
    )

    draw = ImageDraw.Draw(image)

    # random lines
    for _ in range(6):

        draw.line(
            (
                random.randint(0, width),
                random.randint(0, height),
                random.randint(0, width),
                random.randint(0, height)
            ),
            fill=(
                random.randint(150, 220),
                random.randint(150, 220),
                random.randint(150, 220)
            ),
            width=1
        )

    # random dots
    for _ in range(100):

        draw.point(
            (
                random.randint(0, width),
                random.randint(0, height)
            ),
            fill=(
                random.randint(120, 200),
                random.randint(120, 200),
                random.randint(120, 200)
            )
        )

    font = None

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]

    for path in font_paths:

        try:
            font = ImageFont.truetype(path, 40)
            break
        except:
            pass

    if not font:
        font = ImageFont.load_default()

    x = 12

    for char in text:

        color = (
            random.randint(10, 80),
            random.randint(10, 80),
            random.randint(10, 80)
        )

        y = random.randint(8, 15)

        draw.text(
            (x, y),
            char,
            font=font,
            fill=color
        )

        x += 32

    image = image.filter(
        ImageFilter.GaussianBlur(radius=0.5)
    )

    buffer = io.BytesIO()

    image.save(buffer, format="PNG")

    image_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/png;base64,{image_base64}"


# =========================================================
# HOME ROUTE
# =========================================================
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "message": "Axtelica API Running 🚀"
    })


# =========================================================
# CAPTCHA ROUTE
# =========================================================
@app.route("/api/captcha", methods=["GET"])
def captcha():

    try:

        captcha_text = generate_captcha_text()

        captcha_token = make_captcha_token(captcha_text)

        captcha_image = generate_captcha_image(captcha_text)

        print("✅ CAPTCHA GENERATED:", captcha_text)

        return jsonify({
            "success": True,
            "captcha_image": captcha_image,
            "captcha_token": captcha_token
        })

    except Exception as e:

        print("❌ CAPTCHA ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# DEMO ROUTE
# =========================================================
@app.route("/api/demo", methods=["POST"])
def demo():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "No data received"
            }), 400

        # CAPTCHA VERIFY
        captcha_answer = data.get(
            "captchaAnswer",
            ""
        ).strip()

        captcha_token = data.get(
            "captchaToken",
            ""
        ).strip()

        is_valid, captcha_error = verify_captcha_token(
            captcha_token,
            captcha_answer
        )

        if not is_valid:

            return jsonify({
                "success": False,
                "error": captcha_error
            }), 400

        # FORM DATA
        firstName = data.get("firstName", "")
        lastName = data.get("lastName", "")
        company = data.get("company", "")
        email = data.get("email", "")
        phone = data.get("phone", "")
        employees = data.get("employees", "")
        country = data.get("country", "")
        scheduleDemoFor = data.get(
            "scheduleDemoFor",
            ""
        )

        name = f"{firstName} {lastName}"

        extra_fields = f"""
        <tr>
          <td style="font-weight:bold;color:#555;">
          Employees:
          </td>

          <td style="color:#333;">
          {employees}
          </td>
        </tr>

        <tr style="background-color:#f9f9f9;">
          <td style="font-weight:bold;color:#555;">
          Country:
          </td>

          <td style="color:#333;">
          {country}
          </td>
        </tr>

        <tr>
          <td style="font-weight:bold;color:#555;">
          Demo For:
          </td>

          <td style="color:#333;">
          {scheduleDemoFor}
          </td>
        </tr>
        """

        internal_html = internal_email_template(
            title="📩 New Demo Request",
            name=name,
            company=company,
            email=email,
            phone=phone,
            extra_fields=extra_fields
        )

        # Send to sales
        sales_sent = send_email(
            SALES_TO_EMAIL,
            "📩 New Demo Request",
            internal_html,
            reply_to=email
        )

        # Auto response to customer
        customer_sent = send_email(
            email,
            "Thank You for Contacting Axtelica",
            customer_auto_response(name)
        )

        if not sales_sent or not customer_sent:

            return jsonify({
                "success": False,
                "error": "Email sending failed"
            }), 500

        return jsonify({
            "success": True,
            "message": "Demo request submitted successfully"
        })

    except Exception as e:

        print("❌ DEMO ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# CONTACT ROUTE
# =========================================================
@app.route("/api/contact", methods=["POST"])
def contact():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400

        firstName = data.get("firstName", "")
        lastName = data.get("lastName", "")
        email = data.get("email", "")
        company = data.get("company", "")
        phone = data.get("phone", "")
        department = data.get("department", "")
        user_message = data.get("message", "")

        name = f"{firstName} {lastName}"

        extra_fields = f"""
        <tr>
          <td style="font-weight:bold;color:#555;">
          Department:
          </td>

          <td style="color:#333;">
          {department}
          </td>
        </tr>
        """

        message_html = f"""
        <div style="margin-top:20px;">
            <h3 style="color:#111;">
            Message
            </h3>

            <p style="line-height:1.7;color:#444;">
            {user_message}
            </p>
        </div>
        """

        internal_html = internal_email_template(
            title="📩 New Contact Message",
            name=name,
            company=company,
            email=email,
            phone=phone,
            extra_fields=extra_fields,
            message=message_html
        )

        # Send to sales
        sales_sent = send_email(
            SALES_TO_EMAIL,
            "📩 New Contact Message",
            internal_html,
            reply_to=email
        )

        # Auto response to customer
        customer_sent = send_email(
            email,
            "Thank You for Contacting Axtelica",
            customer_auto_response(name)
        )

        if not sales_sent or not customer_sent:

            return jsonify({
                "success": False,
                "error": "Email sending failed"
            }), 500

        return jsonify({
            "success": True,
            "message": "Message sent successfully"
        })

    except Exception as e:

        print("❌ CONTACT ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# PRODUCT ROUTE
# =========================================================
@app.route("/api/product", methods=["POST"])
def product():

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400

        firstName = data.get("firstName", "")
        lastName = data.get("lastName", "")
        company = data.get("company", "")
        email = data.get("email", "")
        phone = data.get("phone", "")
        employees = data.get("employees", "")
        country = data.get("country", "")

        name = f"{firstName} {lastName}"

        extra_fields = f"""
        <tr>
          <td style="font-weight:bold;color:#555;">
          Employees:
          </td>

          <td style="color:#333;">
          {employees}
          </td>
        </tr>

        <tr style="background-color:#f9f9f9;">
          <td style="font-weight:bold;color:#555;">
          Country:
          </td>

          <td style="color:#333;">
          {country}
          </td>
        </tr>
        """

        internal_html = internal_email_template(
            title="📩 New Product Demo Request",
            name=name,
            company=company,
            email=email,
            phone=phone,
            extra_fields=extra_fields
        )

        # Send to sales
        sales_sent = send_email(
            SALES_TO_EMAIL,
            "📩 New Product Demo Request",
            internal_html,
            reply_to=email
        )

        # Auto response to customer
        customer_sent = send_email(
            email,
            "Thank You for Contacting Axtelica",
            customer_auto_response(name)
        )

        if not sales_sent or not customer_sent:

            return jsonify({
                "success": False,
                "error": "Email sending failed"
            }), 500

        return jsonify({
            "success": True,
            "message": "Product demo request sent"
        })

    except Exception as e:

        print("❌ PRODUCT ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# =========================================================
# RUN APP
# =========================================================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )