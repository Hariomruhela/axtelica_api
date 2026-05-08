from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

import os
import smtplib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

# =========================
# FLASK APP
# =========================
app = Flask(__name__)

# ✅ Enable CORS for React frontend
CORS(
    app,
    resources={r"/*": {"origins": "*"}},
    supports_credentials=True
)

# =========================
# SEND EMAIL FUNCTION
# =========================
def send_email(subject, html_content, reply_to=None):

    try:
        msg = MIMEMultipart()

        msg["From"] = "Axtelica <info@axtelica.com>"
        msg["To"] = "hello@techquitoes.com"
        msg["Subject"] = subject

        if reply_to:
            msg["Reply-To"] = reply_to

        msg.attach(MIMEText(html_content, "html"))

        # ✅ Gmail SMTP
        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.ehlo()

        server.starttls()

        server.login(EMAIL_USER, EMAIL_PASS)

        server.sendmail(
            EMAIL_USER,
            "hello@techquitoes.com",
            msg.as_string()
        )

        server.quit()

        print("✅ Email Sent Successfully")

    except Exception as e:
        print("❌ Email Error:", str(e))
        raise e


# =========================
# HOME ROUTE
# =========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "success": True,
        "message": "API Running 🚀"
    })


# =========================
# DEMO API
# =========================
@app.route("/api/demo", methods=["POST"])
def demo():

    try:

        print("✅ API HIT")

        data = request.get_json()

        print("✅ DATA:", data)

        firstName = data.get("firstName")
        lastName = data.get("lastName")
        company = data.get("company")
        email = data.get("email")
        phone = data.get("phone")
        employees = data.get("employees")
        country = data.get("country")
        scheduleDemoFor = data.get("scheduleDemoFor")

        html = f"""
        <h2>🚀 New Demo Request</h2>

        <p><b>Name:</b> {firstName} {lastName}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>company:</b> {company}</p>
        <p><b>Phone:</b> {phone}</p>
        <p><b>Employees:</b> {employees}</p>
        <p><b>Country:</b> {country}</p>
         <p>
                <b>Schedule Demo For:</b>
                {scheduleDemoFor}
            </p>
        <hr style="margin:20px 0;" />
         <p style="font-size:12px;color:gray;">
                Submitted from Axtelica Demo Form
            </p>

        </div>
        """

        print("✅ BEFORE EMAIL")

        send_email(
            "🚀 New Demo Request",
            html,
            email
        )

        print("✅ AFTER EMAIL")

        return jsonify({
            "success": True
        })

    except Exception as e:

        print("❌ FULL ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
# =========================
# CONTACT API
# =========================
@app.route("/api/contact", methods=["POST"])
def contact():

    try:

        print("✅ CONTACT API HIT")

        data = request.get_json()

        print("✅ CONTACT DATA:", data)

        # ✅ Check JSON
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400

        # ✅ Get values
        email = data.get("email", "").strip()
        firstName = data.get("firstName", "").strip()
        lastName = data.get("lastName", "").strip()
        company = data.get("company", "").strip()
        phone = data.get("phone", "").strip()
        department = data.get("department", "").strip()
        message = data.get("message", "").strip()

        # ✅ Validation
        if not firstName:
            return jsonify({
                "success": False,
                "error": "First Name is required"
            }), 400

        if not lastName:
            return jsonify({
                "success": False,
                "error": "Last Name is required"
            }), 400

        if not email:
            return jsonify({
                "success": False,
                "error": "Email is required"
            }), 400

        if not company:
            return jsonify({
                "success": False,
                "error": "Company is required"
            }), 400

        if not phone:
            return jsonify({
                "success": False,
                "error": "Phone is required"
            }), 400

        if not department:
            return jsonify({
                "success": False,
                "error": "Department is required"
            }), 400

        if not message:
            return jsonify({
                "success": False,
                "error": "Message is required"
            }), 400

        # ✅ HTML EMAIL
        html = f"""
        <div style="
            max-width:600px;
            margin:auto;
            font-family:Arial;
            padding:20px;
            border:1px solid #eee;
            border-radius:10px;
        ">

            <h2 style="color:#FF3366;">
                📩 New Contact Message
            </h2>

            <p><b>Name:</b> {firstName} {lastName}</p>

            <p><b>Email:</b> {email}</p>

            <p><b>Company:</b> {company}</p>

            <p><b>Phone:</b> {phone}</p>

            <p><b>Department:</b> {department}</p>

            <hr style="margin:20px 0;" />

            <p><b>Message:</b></p>

            <p>{message}</p>

            <hr style="margin:20px 0;" />

            <p style="font-size:12px;color:gray;">
                Submitted from Axtelica Contact Form
            </p>

        </div>
        """

        print("✅ BEFORE CONTACT EMAIL")

        # ✅ SEND EMAIL
        send_email(
            "📩 New Contact Message",
            html,
            email
        )

        print("✅ AFTER CONTACT EMAIL")

        return jsonify({
            "success": True,
            "message": "Contact message sent successfully"
        })

    except Exception as e:

        print("❌ CONTACT API ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
    

# =========================
# DEMO API for product
# =========================
@app.route("/api/product", methods=["POST"])
def product():

    try:

        print("✅ DEMO API HIT")

        data = request.get_json()

        print("✅ DEMO DATA:", data)

        # ✅ Check JSON
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data received"
            }), 400

        # =========================
        # GET VALUES
        # =========================
        firstName = data.get("firstName", "").strip()
        lastName = data.get("lastName", "").strip()
        company = data.get("company", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        employees = data.get("employees", "").strip()
        country = data.get("country", "").strip()

        # =========================
        # VALIDATION
        # =========================
        if not firstName:
            return jsonify({"success": False, "error": "First Name is required"}), 400

        if not lastName:
            return jsonify({"success": False, "error": "Last Name is required"}), 400

        if not company:
            return jsonify({"success": False, "error": "Company is required"}), 400

        if not email:
            return jsonify({"success": False, "error": "Email is required"}), 400

        if not phone:
            return jsonify({"success": False, "error": "Phone is required"}), 400

        if not employees:
            return jsonify({"success": False, "error": "Employees is required"}), 400

        if not country:
            return jsonify({"success": False, "error": "Country is required"}), 400

        # =========================
        # EMAIL HTML TEMPLATE
        # =========================
        html = f"""
        <div style="
            max-width:600px;
            margin:auto;
            font-family:Arial;
            padding:20px;
            border:1px solid #eee;
            border-radius:10px;
        ">

            <h2 style="color:#FF3366;">
                🚀 New Demo Request From Product Page
            </h2>

            <p><b>Name:</b> {firstName} {lastName}</p>

            <p><b>Company:</b> {company}</p>

            <p><b>Email:</b> {email}</p>

            <p><b>Phone:</b> {phone}</p>

            <p><b>Employees:</b> {employees}</p>

            <p><b>Country:</b> {country}</p>

            <hr style="margin:20px 0;" />

            <p style="font-size:12px;color:gray;">
                Submitted from Axtelica Demo Form
            </p>

        </div>
        """

        print("✅ BEFORE DEMO EMAIL")

        # =========================
        # SEND EMAIL
        # =========================
        send_email(
            "🚀 New Demo Request",
            html,
            email
        )

        print("✅ AFTER DEMO EMAIL")

        return jsonify({
            "success": True,
            "message": "Demo request sent successfully"
        })

    except Exception as e:

        print("❌ DEMO API ERROR:", str(e))

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )