"""
Sample vulnerable Flask application for testing Vulnora.
DO NOT deploy this in production - it contains intentional vulnerabilities.
"""
import os
import sqlite3
import pickle
import hashlib
import subprocess
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# VULN: Hardcoded secret key
SECRET_KEY = "super_secret_key_12345"
DATABASE_PASSWORD = "admin123"
API_KEY = "sk-proj-AAAAAAAAAAAAAAAAAAAAAAAAA"

def get_db():
    """Get database connection."""
    conn = sqlite3.connect("app.db")
    return conn

# VULN: SQL Injection
@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    conn = get_db()
    # Directly interpolating user input into SQL query
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    cursor = conn.execute(query)
    user = cursor.fetchone()
    
    if user:
        return jsonify({"status": "success", "user": user[0]})
    return jsonify({"status": "failed"}), 401

# VULN: Command Injection
@app.route("/ping", methods=["POST"])
def ping_host():
    host = request.json.get("host")
    # User input passed directly to shell command
    result = subprocess.check_output(f"ping -c 1 {host}", shell=True)
    return jsonify({"output": result.decode()})

# VULN: Server-Side Template Injection (SSTI)
@app.route("/greet")
def greet():
    name = request.args.get("name", "World")
    # User input rendered directly in template
    template = f"<h1>Hello {name}!</h1>"
    return render_template_string(template)

# VULN: Insecure Deserialization
@app.route("/load_session", methods=["POST"])
def load_session():
    session_data = request.get_data()
    # Deserializing untrusted data
    user_session = pickle.loads(session_data)
    return jsonify({"session": str(user_session)})

# VULN: Path Traversal
@app.route("/file")
def read_file():
    filename = request.args.get("name")
    # No sanitization of file path
    filepath = os.path.join("/var/data", filename)
    with open(filepath, "r") as f:
        return f.read()

# VULN: Weak cryptography
@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    
    # Using MD5 for password hashing (weak)
    password_hash = hashlib.md5(password.encode()).hexdigest()
    
    conn = get_db()
    conn.execute(
        f"INSERT INTO users (username, password) VALUES ('{username}', '{password_hash}')"
    )
    conn.commit()
    return jsonify({"status": "registered"})

# VULN: Cross-Site Scripting (XSS) via reflected input
@app.route("/search")
def search():
    query = request.args.get("q", "")
    # Reflecting user input without escaping
    return f"<html><body><h2>Results for: {query}</h2></body></html>"

# VULN: Missing authentication on admin endpoint
@app.route("/admin/users")
def admin_users():
    conn = get_db()
    cursor = conn.execute("SELECT id, username FROM users")
    users = [{"id": r[0], "username": r[1]} for r in cursor.fetchall()]
    return jsonify(users)

# VULN: SSRF 
@app.route("/fetch_url", methods=["POST"])
def fetch_url():
    import requests as req
    url = request.json.get("url")
    # Fetching arbitrary URLs without validation
    response = req.get(url)
    return jsonify({"status": response.status_code, "body": response.text[:500]})

# VULN: Debug mode enabled
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
