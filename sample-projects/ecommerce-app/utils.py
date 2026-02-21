"""
Database helper utilities for the e-commerce app.
Contains additional vulnerabilities: Command Injection, Insecure Deserialization, SSRF
"""
import os
import pickle
import subprocess
import requests
import yaml
import tempfile
import base64

# ─── Command Injection ────────────────────────
def ping_server(hostname):
    """Check if a server is reachable"""
    # VULNERABLE: Command injection via unsanitized hostname
    result = os.system(f"ping -c 3 {hostname}")
    return result == 0

def generate_report(report_name):
    """Generate a PDF report"""
    # VULNERABLE: Command injection through subprocess with shell=True
    cmd = f"wkhtmltopdf http://localhost/reports/{report_name} /tmp/{report_name}.pdf"
    subprocess.call(cmd, shell=True)
    return f"/tmp/{report_name}.pdf"

def compress_logs(log_dir):
    """Compress log files"""
    # VULNERABLE: Command injection through os.popen
    output = os.popen(f"tar czf /tmp/logs.tar.gz {log_dir}").read()
    return output

# ─── Insecure Deserialization ─────────────────
def load_user_session(session_data):
    """Restore user session from stored data"""
    # VULNERABLE: Deserializing untrusted data with pickle
    return pickle.loads(base64.b64decode(session_data))

def save_user_session(session_obj):
    """Save user session"""
    return base64.b64encode(pickle.dumps(session_obj)).decode()

def import_product_catalog(catalog_file):
    """Import product catalog from YAML file"""
    with open(catalog_file, 'r') as f:
        # VULNERABLE: yaml.load without SafeLoader allows arbitrary code execution
        catalog = yaml.load(f)
    return catalog

# ─── SSRF (Server-Side Request Forgery) ───────
def fetch_product_image(image_url):
    """Download product image from URL"""
    # VULNERABLE: No URL validation — allows SSRF to internal services
    response = requests.get(image_url)
    return response.content

def check_webhook_url(url):
    """Verify a webhook URL is reachable"""
    # VULNERABLE: SSRF — user-supplied URL fetched server-side
    try:
        resp = requests.get(url, timeout=5)
        return {"status": resp.status_code, "reachable": True}
    except Exception:
        return {"reachable": False}

def fetch_price_feed(feed_url):
    """Fetch product prices from external feed"""
    # VULNERABLE: SSRF with response data returned to user
    response = requests.get(feed_url, timeout=10)
    return response.json()

# ─── Hardcoded Credentials & Tokens ──────────
AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
MONGO_URI = "mongodb://admin:password123@prod-mongo.internal:27017/ecommerce"
JWT_SECRET = "my-super-secret-jwt-key-that-should-be-rotated"
ENCRYPTION_KEY = "aes-256-key-1234567890abcdef"

# ─── Insecure Temp File Handling ──────────────
def process_upload(file_content, filename):
    """Process uploaded file"""
    # VULNERABLE: Predictable temp file + no cleanup
    tmp_path = f"/tmp/upload_{filename}"
    with open(tmp_path, 'wb') as f:
        f.write(file_content)
    # Process file...
    return tmp_path

def create_backup(db_path):
    """Create database backup"""
    # VULNERABLE: World-readable backup created with predictable name
    backup_path = f"/tmp/db_backup_{db_path.replace('/', '_')}"
    os.system(f"cp {db_path} {backup_path}")
    os.chmod(backup_path, 0o777)  # World-readable
    return backup_path

# ─── Weak Cryptography ───────────────────────
def encrypt_sensitive_data(data):
    """Encrypt sensitive data before storage"""
    import hashlib
    # VULNERABLE: Using MD5 for security-critical hashing
    return hashlib.md5(data.encode()).hexdigest()

def generate_token():
    """Generate an authentication token"""
    import random
    # VULNERABLE: Using non-cryptographic random for security tokens
    return ''.join([str(random.randint(0, 9)) for _ in range(16)])

def verify_signature(data, signature):
    """Verify message signature"""
    import hashlib
    # VULNERABLE: SHA1 is deprecated for security use
    computed = hashlib.sha1(data.encode()).hexdigest()
    return computed == signature
