"""
Vulnerable E-Commerce Application
Demonstrates: SQL Injection, XSS, IDOR, Path Traversal, Hardcoded Secrets
"""
from flask import Flask, request, render_template_string, jsonify, send_file, session
import sqlite3
import os
import hashlib

app = Flask(__name__)
app.secret_key = "super_secret_key_12345"  # Hardcoded secret key

# Hardcoded database credentials
DB_HOST = "production-db.internal.company.com"
DB_USER = "admin"
DB_PASSWORD = "P@ssw0rd123!"
API_KEY = "sk-live-PLACEHOLDER-REPLACE-IN-PRODUCTION"
STRIPE_SECRET = "sk_live_PLACEHOLDER_REPLACE_IN_PRODUCTION"  # Demo only

def get_db():
    conn = sqlite3.connect("store.db")
    conn.row_factory = sqlite3.Row
    return conn

# ─── SQL Injection (Classic) ───────────────────
@app.route("/products/search")
def search_products():
    query = request.args.get("q", "")
    db = get_db()
    # VULNERABLE: Direct string concatenation in SQL query
    results = db.execute(
        "SELECT * FROM products WHERE name LIKE '%" + query + "%' OR description LIKE '%" + query + "%'"
    ).fetchall()
    return jsonify([dict(r) for r in results])

# ─── SQL Injection (Login Bypass) ──────────────
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    db = get_db()
    # VULNERABLE: SQL injection allows authentication bypass
    user = db.execute(
        f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    ).fetchone()
    if user:
        session["user_id"] = user["id"]
        session["role"] = user["role"]
        return jsonify({"success": True, "message": "Login successful"})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ─── Stored XSS via Product Reviews ────────────
@app.route("/products/<int:product_id>/review", methods=["POST"])
def add_review(product_id):
    review_text = request.form.get("review")
    username = request.form.get("name", "Anonymous")
    db = get_db()
    db.execute("INSERT INTO reviews (product_id, username, text) VALUES (?, ?, ?)",
               (product_id, username, review_text))
    db.commit()
    return jsonify({"success": True})

@app.route("/products/<int:product_id>/reviews")
def show_reviews(product_id):
    db = get_db()
    reviews = db.execute("SELECT * FROM reviews WHERE product_id = ?", (product_id,)).fetchall()
    # VULNERABLE: Rendering user input without escaping — Stored XSS
    html = "<h2>Reviews</h2>"
    for r in reviews:
        html += f"<div class='review'><b>{r['username']}</b>: {r['text']}</div>"
    return render_template_string(html)

# ─── IDOR (Insecure Direct Object Reference) ──
@app.route("/api/orders/<int:order_id>")
def get_order(order_id):
    db = get_db()
    # VULNERABLE: No authorization check — any user can view any order
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if order:
        return jsonify(dict(order))
    return jsonify({"error": "Order not found"}), 404

@app.route("/api/users/<int:user_id>/profile")
def get_profile(user_id):
    db = get_db()
    # VULNERABLE: No authentication check — exposes all user data including payment info
    user = db.execute(
        "SELECT id, username, email, phone, address, credit_card, ssn FROM users WHERE id = ?"
        , (user_id,)
    ).fetchone()
    return jsonify(dict(user))

# ─── Path Traversal ───────────────────────────
@app.route("/download")
def download_file():
    filename = request.args.get("file")
    # VULNERABLE: No path sanitization — allows directory traversal
    filepath = os.path.join("/var/www/uploads", filename)
    return send_file(filepath)

@app.route("/api/invoices/<path:invoice_path>")
def get_invoice(invoice_path):
    # VULNERABLE: Path parameter allows traversal with ../
    full_path = f"/var/www/invoices/{invoice_path}"
    with open(full_path, "r") as f:
        return f.read()

# ─── Weak Password Hashing ────────────────────
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    # VULNERABLE: MD5 is cryptographically broken for password hashing
    password_hash = hashlib.md5(password.encode()).hexdigest()
    db = get_db()
    db.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password_hash))
    db.commit()
    return jsonify({"success": True})

# ─── Mass Assignment ──────────────────────────
@app.route("/api/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    db = get_db()
    # VULNERABLE: Allows updating any field including 'role' and 'is_admin'
    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    values = list(data.values()) + [user_id]
    db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    db.commit()
    return jsonify({"success": True})

# ─── Server-Side Template Injection ───────────
@app.route("/welcome")
def welcome():
    name = request.args.get("name", "Guest")
    # VULNERABLE: User input directly in template — SSTI
    template = f"<h1>Welcome {name}!</h1><p>Thank you for shopping with us.</p>"
    return render_template_string(template)

# ─── Insecure Cookie Configuration ────────────
@app.route("/set-preferences", methods=["POST"])
def set_preferences():
    from flask import make_response
    resp = make_response(jsonify({"success": True}))
    # VULNERABLE: Cookie without Secure, HttpOnly, or SameSite flags
    resp.set_cookie("user_prefs", request.form.get("prefs", ""), max_age=31536000)
    resp.set_cookie("session_token", session.get("user_id", ""), max_age=31536000)
    return resp

if __name__ == "__main__":
    # VULNERABLE: Debug mode enabled in production
    app.run(debug=True, host="0.0.0.0", port=5000)
