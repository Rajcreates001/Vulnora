"""Code parsing utilities using Tree-sitter and basic AST analysis."""

import re
from typing import Any, Dict, List, Optional


def parse_code_structure(content: str, language: str) -> Dict[str, Any]:
    """Parse code to extract structural information without requiring tree-sitter binaries."""
    structure: Dict[str, Any] = {
        "functions": [],
        "classes": [],
        "imports": [],
        "routes": [],
        "database_calls": [],
        "auth_patterns": [],
        "sensitive_patterns": [],
        "hardcoded_secrets": [],
    }

    lines = content.split("\n")

    if language == "python":
        structure = _parse_python(lines, structure)
    elif language in ("javascript", "typescript"):
        structure = _parse_javascript(lines, structure)
    elif language == "java":
        structure = _parse_java(lines, structure)
    else:
        structure = _parse_generic(lines, structure)

    # Universal patterns
    structure["hardcoded_secrets"] = _find_hardcoded_secrets(lines)
    structure["sensitive_patterns"] = _find_sensitive_patterns(lines)

    return structure


def _parse_python(lines: List[str], structure: Dict[str, Any]) -> Dict[str, Any]:
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Functions
        if stripped.startswith("def "):
            match = re.match(r"def\s+(\w+)\s*\(", stripped)
            if match:
                structure["functions"].append({"name": match.group(1), "line": i, "type": "function"})

        # Classes
        if stripped.startswith("class "):
            match = re.match(r"class\s+(\w+)", stripped)
            if match:
                structure["classes"].append({"name": match.group(1), "line": i})

        # Imports
        if stripped.startswith("import ") or stripped.startswith("from "):
            structure["imports"].append({"statement": stripped, "line": i})

        # Routes (Flask/FastAPI)
        if re.search(r'@(app|router)\.(get|post|put|delete|patch)\s*\(', stripped):
            route_match = re.search(r'["\']([^"\']+)["\']', stripped)
            if route_match:
                structure["routes"].append({"path": route_match.group(1), "line": i})

        # Database calls
        if re.search(r'(execute|cursor|query|fetchone|fetchall|\.filter|\.all\(\)|\.raw\()', stripped):
            structure["database_calls"].append({"line": i, "code": stripped})

        # Auth patterns
        if re.search(r'(password|token|auth|login|session|jwt|bcrypt|hash)', stripped, re.I):
            structure["auth_patterns"].append({"line": i, "code": stripped})

    return structure


def _parse_javascript(lines: List[str], structure: Dict[str, Any]) -> Dict[str, Any]:
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Functions
        fn_patterns = [
            r'function\s+(\w+)\s*\(',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?\(',
            r'const\s+(\w+)\s*=\s*(?:async\s+)?function',
            r'(\w+)\s*:\s*(?:async\s+)?function',
        ]
        for pat in fn_patterns:
            match = re.search(pat, stripped)
            if match:
                structure["functions"].append({"name": match.group(1), "line": i, "type": "function"})
                break

        # Imports
        if stripped.startswith("import ") or stripped.startswith("require("):
            structure["imports"].append({"statement": stripped, "line": i})

        # Routes (Express)
        if re.search(r'(app|router)\.(get|post|put|delete|patch)\s*\(', stripped):
            route_match = re.search(r'["\']([^"\']+)["\']', stripped)
            if route_match:
                structure["routes"].append({"path": route_match.group(1), "line": i})

        # Database calls
        if re.search(r'(\.query|\.execute|\.find|\.findOne|\.aggregate|\.raw|knex|prisma|sequelize)', stripped, re.I):
            structure["database_calls"].append({"line": i, "code": stripped})

        # innerHTML / DOM manipulation
        if re.search(r'(innerHTML|outerHTML|document\.write|eval\(|\.html\()', stripped):
            structure["database_calls"].append({"line": i, "code": stripped})

        # Auth patterns
        if re.search(r'(password|token|auth|login|session|jwt|bcrypt|hash)', stripped, re.I):
            structure["auth_patterns"].append({"line": i, "code": stripped})

    return structure


def _parse_java(lines: List[str], structure: Dict[str, Any]) -> Dict[str, Any]:
    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Methods
        match = re.search(r'(public|private|protected)\s+\w+\s+(\w+)\s*\(', stripped)
        if match:
            structure["functions"].append({"name": match.group(2), "line": i, "type": "method"})

        # Classes
        match = re.search(r'class\s+(\w+)', stripped)
        if match:
            structure["classes"].append({"name": match.group(1), "line": i})

        # Imports
        if stripped.startswith("import "):
            structure["imports"].append({"statement": stripped, "line": i})

        # Spring routes
        if re.search(r'@(Get|Post|Put|Delete|Request)Mapping', stripped):
            route_match = re.search(r'["\']([^"\']+)["\']', stripped)
            if route_match:
                structure["routes"].append({"path": route_match.group(1), "line": i})

        # Database
        if re.search(r'(PreparedStatement|Statement|createQuery|nativeQuery|executeQuery)', stripped):
            structure["database_calls"].append({"line": i, "code": stripped})

    return structure


def _parse_generic(lines: List[str], structure: Dict[str, Any]) -> Dict[str, Any]:
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.search(r'function\s+\w+|def\s+\w+', stripped):
            match = re.search(r'(?:function|def)\s+(\w+)', stripped)
            if match:
                structure["functions"].append({"name": match.group(1), "line": i, "type": "function"})
    return structure


def _find_hardcoded_secrets(lines: List[str]) -> List[Dict[str, Any]]:
    secrets = []
    patterns = [
        (r'(?:api[_-]?key|apikey)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{16,}["\']', "API Key"),
        (r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']{4,}["\']', "Password"),
        (r'(?:secret|token)\s*[:=]\s*["\'][a-zA-Z0-9_\-]{8,}["\']', "Secret/Token"),
        (r'(?:aws_access_key|aws_secret)\s*[:=]\s*["\'][A-Za-z0-9/+=]{16,}["\']', "AWS Key"),
        (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Private Key"),
        (r'(?:ghp_|gho_|github_pat_)[a-zA-Z0-9_]{36,}', "GitHub Token"),
        (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API Key"),
    ]
    for i, line in enumerate(lines, 1):
        for pattern, secret_type in patterns:
            if re.search(pattern, line, re.I):
                secrets.append({"line": i, "type": secret_type, "code": line.strip()})
    return secrets


def _find_sensitive_patterns(lines: List[str]) -> List[Dict[str, Any]]:
    patterns_found = []
    sensitive = [
        (r'os\.system\s*\(', "Command Execution"),
        (r'subprocess\.(call|run|Popen)\s*\(', "Subprocess Call"),
        (r'eval\s*\(', "Eval Usage"),
        (r'exec\s*\(', "Exec Usage"),
        (r'pickle\.loads?\s*\(', "Pickle Deserialization"),
        (r'yaml\.load\s*\(', "Unsafe YAML Load"),
        (r'render_template_string\s*\(', "Template Injection Risk"),
        (r'dangerouslySetInnerHTML', "Dangerous HTML Injection"),
        (r'__import__\s*\(', "Dynamic Import"),
    ]
    for i, line in enumerate(lines, 1):
        for pattern, desc in sensitive:
            if re.search(pattern, line):
                patterns_found.append({"line": i, "type": desc, "code": line.strip()})
    return patterns_found
