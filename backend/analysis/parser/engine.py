import os
from typing import Dict, List, Any

# Delay importing so we don't crash if they aren't installed globally yet
# tree_sitter structure parsing

def analyze_file(filename: str, content: str) -> Dict[str, Any]:
    """Parse file content into AST and extract structured meaning."""
    try:
        import tree_sitter_python
        import tree_sitter_javascript
        from tree_sitter import Language, Parser
    except ImportError:
        return {"filename": filename, "functions": [], "status": "no_parser"}

    PY_LANGUAGE = Language(tree_sitter_python.language())
    JS_LANGUAGE = Language(tree_sitter_javascript.language())

    ext = os.path.splitext(filename)[1].lower()
    parser = Parser()
    
    lang_name = "unknown"
    if ext == ".py":
        parser.language = PY_LANGUAGE
        lang_name = "python"
        query_str = "(function_definition name: (identifier) @name)"
    elif ext in [".js", ".jsx", ".ts", ".tsx"]:
        parser.language = JS_LANGUAGE
        lang_name = "javascript" if "j" in ext else "typescript"
        query_str = """
            (function_declaration name: (identifier) @name)
            (variable_declarator name: (identifier) @name value: (arrow_function))
        """
    else:
        return {"filename": filename, "functions": [], "status": "unsupported"}
    
    source_bytes = content.encode("utf8")
    tree = parser.parse(source_bytes)
    
    functions = []
    try:
        query = parser.language.query(query_str)
        captures = query.captures(tree.root_node)
        for capture, _ in captures:
            # Basic function extraction
            functions.append({
                "name": capture.text.decode("utf8") if hasattr(capture, "text") else "unknown",
                "start_line": capture.start_point[0] if hasattr(capture, "start_point") else 0
            })
    except Exception as e:
        pass # If query fails, just continue
        
    return {
        "filename": filename,
        "language": lang_name,
        "functions": functions,
        "status": "parsed"
    }

def collect_ast_data(project_dir: str) -> List[Dict[str, Any]]:
    """Walk directories and collect AST representation of the codebase."""
    results = []
    ignored = {"node_modules", ".git", ".venv", "__pycache__"}
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d not in ignored]
        for f in files:
            filepath = os.path.join(root, f)
            if filepath.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        content = file.read()
                    ast_data = analyze_file(filepath.replace(project_dir, "").lstrip("/\\"), content)
                    results.append(ast_data)
                except Exception:
                    continue
    return results
