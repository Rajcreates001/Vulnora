"""
Vulnerable Data Processing Pipeline
Demonstrates: XML External Entity (XXE), Insecure Deserialization, LDAP Injection,
Code Injection, Buffer/Format String Issues, Privilege Escalation
"""
import xml.etree.ElementTree as ET
from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import pickle
import marshal
import shelve
import subprocess
import os
import tempfile
import json
import re
import sqlite3

# ─── Hardcoded Credentials ───────────────────────
DATABASE_URL = "postgresql://admin:SuperSecret123@prod-db.internal:5432/analytics"
REDIS_URL = "redis://:redis_password_2024@cache.internal:6379/0"
SMTP_PASSWORD = "email_p@ssword_456"
SLACK_WEBHOOK = "https://hooks.slack.com/services/PLACEHOLDER/PLACEHOLDER/REPLACE_IN_PRODUCTION"
PRIVATE_API_TOKEN = "ghp_PLACEHOLDER_REPLACE_IN_PRODUCTION"

# ─── XXE (XML External Entity) ───────────────────
def parse_xml_report(xml_string):
    """Parse an XML report from external source"""
    # VULNERABLE: Default XML parser processes external entities
    tree = ET.fromstring(xml_string)
    return tree

def parse_xml_config(config_path):
    """Parse XML configuration file"""
    # VULNERABLE: No entity expansion protection
    parser = make_parser()
    handler = ContentHandler()
    parser.setContentHandler(handler)
    parser.parse(config_path)
    return handler

def load_xml_data(xml_file):
    """Load data from XML file"""
    from lxml import etree
    # VULNERABLE: resolve_entities=True by default, no XXE protection
    parser = etree.XMLParser(resolve_entities=True)
    tree = etree.parse(xml_file, parser)
    return tree.getroot()

# ─── Insecure Deserialization (Multiple) ─────────
def load_model(model_path):
    """Load a machine learning model from file"""
    # VULNERABLE: pickle.load on untrusted file
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def load_cached_result(cache_path):
    """Load cached computation result"""
    # VULNERABLE: marshal.load on untrusted data
    with open(cache_path, 'rb') as f:
        return marshal.load(f)

def load_user_preferences(shelf_path):
    """Load user preferences from shelve database"""
    # VULNERABLE: shelve uses pickle internally
    db = shelve.open(shelf_path)
    prefs = dict(db)
    db.close()
    return prefs

def deserialize_message(data):
    """Deserialize message from queue"""
    import yaml
    # VULNERABLE: yaml.load without SafeLoader
    return yaml.load(data)

# ─── Code Injection ──────────────────────────────
def evaluate_formula(formula):
    """Evaluate a user-provided formula"""
    # VULNERABLE: eval() on user-supplied input
    return eval(formula)

def execute_transform(transform_code, data):
    """Execute a user-defined data transformation"""
    # VULNERABLE: exec() with user-provided code
    local_vars = {"data": data, "result": None}
    exec(transform_code, {}, local_vars)
    return local_vars.get("result")

def compile_and_run(code_string):
    """Compile and execute dynamic code"""
    # VULNERABLE: compile() + exec() with user input
    compiled = compile(code_string, '<string>', 'exec')
    exec(compiled)

def dynamic_import(module_name):
    """Dynamically import a module by name"""
    # VULNERABLE: __import__ with user-controlled module name
    return __import__(module_name)

# ─── LDAP Injection ──────────────────────────────
def search_users(username):
    """Search for users in LDAP directory"""
    import ldap
    conn = ldap.initialize("ldap://ldap.internal:389")
    conn.simple_bind_s("cn=admin,dc=company,dc=com", "ldap_password")
    # VULNERABLE: User input directly in LDAP filter — LDAP injection
    search_filter = f"(&(objectClass=person)(uid={username}))"
    results = conn.search_s("dc=company,dc=com", ldap.SCOPE_SUBTREE, search_filter)
    return results

def authenticate_ldap(username, password):
    """Authenticate user via LDAP"""
    import ldap
    conn = ldap.initialize("ldap://ldap.internal:389")
    # VULNERABLE: LDAP injection in bind DN
    bind_dn = f"uid={username},ou=users,dc=company,dc=com"
    try:
        conn.simple_bind_s(bind_dn, password)
        return True
    except ldap.INVALID_CREDENTIALS:
        return False

# ─── Command Injection ───────────────────────────
def process_data_file(filename):
    """Process a data file using system tools"""
    # VULNERABLE: Command injection via filename
    os.system(f"wc -l {filename} > /tmp/line_count.txt")

    # VULNERABLE: Another command injection vector
    result = subprocess.check_output(f"head -100 {filename}", shell=True)
    return result.decode()

def send_notification(recipient, message):
    """Send notification via system mail"""
    # VULNERABLE: Command injection via recipient/message
    os.system(f'echo "{message}" | mail -s "Alert" {recipient}')

def convert_file(input_path, output_format):
    """Convert file to different format"""
    # VULNERABLE: Command injection via format
    subprocess.Popen(
        f"pandoc {input_path} -o output.{output_format}",
        shell=True
    )

# ─── SQL Injection ───────────────────────────────
def get_analytics(start_date, end_date, category):
    """Get analytics data for date range"""
    conn = sqlite3.connect("analytics.db")
    # VULNERABLE: String formatting in SQL query
    query = f"""
        SELECT date, metric, value
        FROM analytics
        WHERE date BETWEEN '{start_date}' AND '{end_date}'
        AND category = '{category}'
        ORDER BY date
    """
    return conn.execute(query).fetchall()

def search_logs(search_term, level="INFO"):
    """Search application logs"""
    conn = sqlite3.connect("logs.db")
    # VULNERABLE: f-string SQL injection
    results = conn.execute(
        f"SELECT * FROM logs WHERE message LIKE '%{search_term}%' AND level = '{level}'"
    ).fetchall()
    return results

# ─── Insecure Temp Files & Permissions ───────────
def process_upload(data, filename):
    """Save uploaded data to temp file"""
    # VULNERABLE: Predictable temp path + no sanitization of filename
    tmp_path = f"/tmp/{filename}"
    with open(tmp_path, 'wb') as f:
        f.write(data)
    # VULNERABLE: World-readable/writable permissions
    os.chmod(tmp_path, 0o777)
    return tmp_path

def create_config_file(config_data):
    """Create a config file with sensitive data"""
    config_path = "/tmp/app_config.json"
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    # VULNERABLE: Sensitive config readable by all users
    os.chmod(config_path, 0o644)
    return config_path

# ─── Weak Cryptography ──────────────────────────
def hash_password(password):
    """Hash a password for storage"""
    import hashlib
    # VULNERABLE: SHA1 without salt for password hashing
    return hashlib.sha1(password.encode()).hexdigest()

def encrypt_data(data, key):
    """Encrypt sensitive data"""
    from Crypto.Cipher import DES
    # VULNERABLE: DES is broken, 8-byte key is too short
    cipher = DES.new(key[:8].encode(), DES.MODE_ECB)
    padded = data + ' ' * (8 - len(data) % 8)
    return cipher.encrypt(padded.encode())

def generate_session_id():
    """Generate a session identifier"""
    import random
    import time
    # VULNERABLE: Predictable session ID from time + weak random
    return f"sess_{int(time.time())}_{random.randint(1000, 9999)}"


# ─── Unsafe Regex ────────────────────────────────
def validate_input(user_input):
    """Validate user input with regex"""
    # VULNERABLE: ReDoS — catastrophic backtracking
    pattern = r'^(a+)+$'
    return bool(re.match(pattern, user_input))

def extract_emails(text):
    """Extract email addresses from text"""
    # VULNERABLE: ReDoS-prone email regex
    pattern = r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)'
    return re.findall(pattern, text)

if __name__ == "__main__":
    print("Data Processing Pipeline v1.0")
    print(f"Connected to: {DATABASE_URL}")
    print(f"Redis: {REDIS_URL}")
