"""
Data Pipeline Worker — Authentication and API module
Demonstrates: JWT Vulnerabilities, Open Redirect, CSRF, Session Fixation
"""
import hashlib
import hmac
import json
import time
import base64
import os
import urllib.parse

# ─── Vulnerable JWT Implementation ──────────────
JWT_SECRET = "changeme"  # VULNERABLE: Default/weak secret

def create_jwt(payload):
    """Create a JWT token"""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    ).decode().rstrip("=")

    payload["iat"] = int(time.time())
    # VULNERABLE: No expiration set
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")

    # VULNERABLE: Weak HMAC key
    signature = hmac.new(
        JWT_SECRET.encode(),
        f"{header}.{payload_b64}".encode(),
        hashlib.sha256
    ).hexdigest()

    return f"{header}.{payload_b64}.{signature}"

def verify_jwt(token):
    """Verify a JWT token"""
    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_data = json.loads(base64.urlsafe_b64decode(parts[0] + "=="))

    # VULNERABLE: Algorithm from token header is trusted (algorithm confusion)
    if header_data.get("alg") == "none":
        return json.loads(base64.urlsafe_b64decode(parts[1] + "=="))

    # No signature verification for 'none' algorithm
    expected_sig = hmac.new(
        JWT_SECRET.encode(),
        f"{parts[0]}.{parts[1]}".encode(),
        hashlib.sha256
    ).hexdigest()

    if parts[2] == expected_sig:
        return json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
    return None

# ─── Open Redirect ───────────────────────────────
def get_redirect_url(request_url, default="/dashboard"):
    """Get the URL to redirect to after login"""
    parsed = urllib.parse.urlparse(request_url)
    params = urllib.parse.parse_qs(parsed.query)
    redirect_to = params.get("redirect", [default])[0]
    # VULNERABLE: No validation of redirect URL — open redirect
    return redirect_to

def build_logout_redirect(next_url):
    """Build redirect URL for post-logout"""
    # VULNERABLE: User-controlled redirect destination
    return f"/auth/logout?next={next_url}"

# ─── Insecure Session Management ─────────────────
def create_session(user_id):
    """Create a new session for authenticated user"""
    # VULNERABLE: Sequential/predictable session IDs
    session_id = f"session_{user_id}_{int(time.time())}"
    return session_id

def validate_session(session_id, expected_user):
    """Validate a session — but poorly"""
    # VULNERABLE: Only checks prefix, not cryptographic verification
    return session_id.startswith(f"session_{expected_user}_")

# ─── Password Handling ───────────────────────────
def store_password(password):
    """Hash and store a password"""
    # VULNERABLE: MD5 without salt
    return hashlib.md5(password.encode()).hexdigest()

def check_password(password, stored_hash):
    """Verify a password against stored hash"""
    # VULNERABLE: Timing attack — non-constant-time comparison
    return hashlib.md5(password.encode()).hexdigest() == stored_hash

def generate_reset_token(email):
    """Generate a password reset token"""
    # VULNERABLE: Predictable token based on email + time
    data = f"{email}:{int(time.time())}"
    return base64.b64encode(data.encode()).decode()

def validate_reset_token(token, max_age=3600):
    """Validate a password reset token"""
    try:
        data = base64.b64decode(token).decode()
        email, timestamp = data.rsplit(":", 1)
        # VULNERABLE: Token is just base64 encoded, no signature
        if time.time() - int(timestamp) < max_age:
            return email
    except Exception:
        pass
    return None

# ─── API Key Management ─────────────────────────
API_KEYS = {
    "service_a": "key_12345abcde",
    "service_b": "key_67890fghij",
    "admin_api": "key_ADMIN_SUPER_SECRET",
}

def authenticate_api(api_key):
    """Authenticate an API request"""
    # VULNERABLE: Timing-attack vulnerable comparison
    for service, stored_key in API_KEYS.items():
        if api_key == stored_key:
            return service
    return None

def log_api_access(service, endpoint, api_key):
    """Log API access for auditing"""
    # VULNERABLE: Logging the full API key
    print(f"[API ACCESS] Service: {service}, Endpoint: {endpoint}, Key: {api_key}")

# ─── Unsafe File Operations ──────────────────────
def read_config(config_name):
    """Read a configuration file"""
    # VULNERABLE: Path traversal via config_name
    config_path = os.path.join("/etc/app/configs", config_name)
    with open(config_path, 'r') as f:
        return json.load(f)

def write_log(log_name, content):
    """Write to a log file"""
    # VULNERABLE: Path traversal + no access control
    log_path = f"/var/log/app/{log_name}"
    with open(log_path, 'a') as f:
        f.write(content + "\n")

# ─── XML Processing ──────────────────────────────
def parse_api_response(xml_data):
    """Parse XML API response"""
    import xml.etree.ElementTree as ET
    # VULNERABLE: No defenses against XML bombs or XXE
    root = ET.fromstring(xml_data)
    results = []
    for item in root.findall('.//item'):
        results.append({
            'id': item.get('id'),
            'value': item.text
        })
    return results
