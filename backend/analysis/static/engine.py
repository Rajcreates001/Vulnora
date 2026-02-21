import subprocess
import json
import os
from typing import List, Dict, Any

def run_static_analysis(directory: str) -> List[Dict[str, Any]]:
    """Execute static deterministic analysis tools (e.g. bandit)."""
    results = []
    results.extend(_run_bandit(directory))
    return results

def _run_bandit(directory: str) -> List[Dict[str, Any]]:
    """Run bandit against python files in the directory."""
    results = []
    try:
        # Running bandit recursively 
        cmd = ["python", "-m", "bandit", "-r", directory, "-f", "json"]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        # Bandit returns non-zero if issues found, but JSON output is still printed
        if proc.stdout and "{" in proc.stdout:
            try:
                # Output might have trailing lines, isolate JSON
                json_start = proc.stdout.find("{")
                json_end = proc.stdout.rfind("}") + 1
                data = json.loads(proc.stdout[json_start:json_end])
                
                for r in data.get("results", []):
                    # Convert to normalized finding format
                    file_path = r.get("filename", "").replace(directory, "").lstrip("/\\")
                    results.append({
                        "id": r.get("test_id"),
                        "severity": r.get("issue_severity", "LOW").upper(),
                        "confidence": r.get("issue_confidence", "LOW").upper(),
                        "file": file_path,
                        "line": r.get("line_number"),
                        "title": r.get("test_name", "Bandit Finding"),
                        "description": r.get("issue_text", ""),
                        "source": "SAST: Bandit"
                    })
            except json.JSONDecodeError:
                pass
    except Exception as e:
        print(f"Bandit static analysis failed: {e}")
        
    return results
