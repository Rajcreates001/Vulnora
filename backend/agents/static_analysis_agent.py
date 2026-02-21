"""Static Analysis Agent — Integrates Semgrep/Bandit and correlates findings."""

import json
import subprocess
import tempfile
import os
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress

SYSTEM_PROMPT = """You are a static analysis security expert. You receive source code files and raw findings from static analysis tools.

Your job is to:
1. Analyze the ACTUAL CODE provided — look at every function, every import, every pattern
2. Find vulnerabilities that are SPECIFIC to THIS codebase — reference exact file names, function names, variable names, and line numbers
3. Correlate raw tool findings with the code context to remove false positives
4. Identify security patterns that automated tools miss (logic flaws, auth bypasses, data leaks)
5. Rate confidence level based on how certain you are

CRITICAL: Your findings MUST reference the actual code. Include the exact vulnerable code snippet, the exact file path, and explain WHY it's vulnerable in the context of THIS specific application. Do not give generic descriptions.

Output valid JSON:
{
    "findings": [
        {
            "title": "Specific descriptive title referencing the actual vulnerability",
            "type": "vulnerability category",
            "severity": "Critical|High|Medium|Low",
            "file_path": "exact/file/path.py",
            "line_start": N,
            "line_end": N,
            "code_snippet": "the exact vulnerable code from the file",
            "description": "Detailed description explaining what's wrong and how it can be exploited in THIS codebase",
            "cwe_id": "CWE-XXX",
            "confidence": 0-100,
            "tool_source": "ai_analysis|bandit|pattern_analysis",
            "is_false_positive": false,
            "reasoning": "Why this is a real vulnerability in the context of this application"
        }
    ],
    "summary": "Summary of security posture specific to this codebase"
}"""


class StaticAnalysisAgent(BaseAgent):
    name = "static_analysis_agent"
    description = "Runs static analysis tools and correlates findings"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        files = state.get("files", [])

        await self.log(project_id, f"Starting static analysis on {len(files)} files")
        await update_scan_progress(project_id, "analysis", self.name, 0.1, "Running static analysis tools...")

        # Run tools on Python files
        bandit_results = await self._run_bandit(files, project_id)
        await update_scan_progress(project_id, "analysis", self.name, 0.3, f"Bandit found {len(bandit_results)} issues")

        # Run pattern-based analysis for all files
        pattern_results = self._run_pattern_analysis(files)
        await update_scan_progress(project_id, "analysis", self.name, 0.5, f"Pattern analysis found {len(pattern_results)} issues, correlating with AI...")

        # Send FULL code to LLM for deep AI-driven static analysis
        # Process files in batches to fit context windows
        all_findings = []
        batch_size = 8
        file_batches = [files[i:i+batch_size] for i in range(0, len(files), batch_size)]

        for batch_idx, batch in enumerate(file_batches):
            progress = 0.5 + (0.4 * (batch_idx / max(len(file_batches), 1)))
            await update_scan_progress(project_id, "analysis", self.name, progress, f"AI analyzing batch {batch_idx+1}/{len(file_batches)}...")

            # Build full code context for this batch
            code_context = self._build_full_code_context(batch)

            # Include relevant tool findings for these files
            batch_files = {f["file_path"] for f in batch}
            relevant_bandit = [r for r in bandit_results if r.get("file_path") in batch_files]
            relevant_patterns = [r for r in pattern_results if r.get("file_path") in batch_files]

            user_prompt = f"""Analyze these source code files for security vulnerabilities.
You MUST analyze the actual code content below and find vulnerabilities SPECIFIC to this code.

SOURCE CODE FILES:
{code_context}

BANDIT TOOL FINDINGS FOR THESE FILES:
{json.dumps(relevant_bandit, indent=2) if relevant_bandit else "No Bandit findings for these files."}

PATTERN ANALYSIS FINDINGS FOR THESE FILES:
{json.dumps(relevant_patterns, indent=2) if relevant_patterns else "No pattern findings for these files."}

Instructions:
- Analyze EVERY file above for security issues
- Reference exact file paths, function names, and line numbers from the code
- Include the actual vulnerable code snippet
- Explain the vulnerability in context of this specific application
- Do NOT generate generic findings — every finding must map to actual code above
- Verify and filter the tool findings against the actual code"""

            try:
                response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=4096)
                batch_results = json.loads(response)
                batch_findings = batch_results.get("findings", [])
                # Only keep findings that reference actual files in the batch
                for f in batch_findings:
                    if f.get("file_path") in batch_files or not f.get("is_false_positive", False):
                        all_findings.append(f)
            except Exception as e:
                await self.log(project_id, f"AI analysis batch {batch_idx+1} fallback: {str(e)}", "warning")
                # For fallback, use the tool findings which are already file-specific
                all_findings.extend(relevant_bandit)
                all_findings.extend(relevant_patterns)

        # Deduplicate findings
        seen = set()
        unique_findings = []
        for f in all_findings:
            key = (f.get("file_path", ""), f.get("line_start", 0), f.get("title", ""))
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        analysis_results = {
            "findings": unique_findings,
            "summary": f"Analyzed {len(files)} files. Found {len(unique_findings)} security findings across the codebase.",
        }

        await self.save_output(project_id, analysis_results)
        await self.log(project_id, f"Static analysis complete: {len(unique_findings)} findings from {len(files)} files", "success")
        await update_scan_progress(project_id, "analysis", self.name, 1.0, "Static analysis complete")

        state["static_analysis_results"] = analysis_results
        return state

    async def _run_bandit(self, files: List[Dict], project_id: str) -> List[Dict]:
        """Run Bandit on Python files."""
        python_files = [f for f in files if f.get("language") == "python"]
        if not python_files:
            return []

        # Find bandit executable — check PATH first, then common user install locations
        import shutil
        bandit_cmd = shutil.which("bandit")
        if not bandit_cmd:
            # Try common user-install locations on Windows
            user_scripts = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "Python", "Python313", "Scripts", "bandit.exe")
            if os.path.exists(user_scripts):
                bandit_cmd = user_scripts
            else:
                # Try python -m bandit as last resort
                bandit_cmd = None

        results = []
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                for f in python_files:
                    fpath = os.path.join(tmpdir, os.path.basename(f["file_path"]))
                    with open(fpath, "w", encoding="utf-8") as fh:
                        fh.write(f.get("content", ""))

                if bandit_cmd:
                    cmd = [bandit_cmd, "-r", tmpdir, "-f", "json", "-q"]
                else:
                    cmd = ["python", "-m", "bandit", "-r", tmpdir, "-f", "json", "-q"]

                proc = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=60,
                )
                if proc.stdout:
                    bandit_data = json.loads(proc.stdout)
                    for result in bandit_data.get("results", []):
                        results.append({
                            "title": result.get("test_name", "Unknown"),
                            "type": result.get("test_id", ""),
                            "severity": self._map_severity(result.get("issue_severity", "MEDIUM")),
                            "file_path": self._map_file_path(result.get("filename", ""), python_files),
                            "line_start": result.get("line_number", 0),
                            "line_end": result.get("line_number", 0),
                            "code_snippet": result.get("code", ""),
                            "description": result.get("issue_text", ""),
                            "confidence": self._map_confidence(result.get("issue_confidence", "MEDIUM")),
                            "tool_source": "bandit",
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            await self.log(project_id, f"Bandit not available or failed: {str(e)}", "warning")

        return results

    def _run_pattern_analysis(self, files: List[Dict]) -> List[Dict]:
        """Run regex-based pattern analysis on actual file contents."""
        import re
        findings = []
        dangerous_patterns = [
            (r'eval\s*\(', "Code Injection via eval()", "Critical", "CWE-94"),
            (r'exec\s*\(', "Code Injection via exec()", "Critical", "CWE-94"),
            (r'os\.system\s*\(', "OS Command Injection", "Critical", "CWE-78"),
            (r'subprocess\.(call|run|Popen)\s*\(.*shell\s*=\s*True', "Shell Injection", "Critical", "CWE-78"),
            (r'pickle\.loads?\s*\(', "Insecure Deserialization", "High", "CWE-502"),
            (r'yaml\.load\s*\([^)]*\)(?!.*Loader)', "Unsafe YAML Deserialization", "High", "CWE-502"),
            (r'render_template_string\s*\(', "Server Side Template Injection", "Critical", "CWE-1336"),
            (r'innerHTML\s*=', "Cross-Site Scripting via innerHTML", "High", "CWE-79"),
            (r'dangerouslySetInnerHTML', "XSS via dangerouslySetInnerHTML", "High", "CWE-79"),
            (r'document\.write\s*\(', "DOM-based XSS via document.write", "High", "CWE-79"),
            (r'SELECT.*\+.*(?:request|params|query|input|user)', "SQL Injection (String Concatenation)", "Critical", "CWE-89"),
            (r'\.query\s*\(\s*[f"\'].*\{', "SQL Injection (f-string)", "Critical", "CWE-89"),
            (r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded Secret", "High", "CWE-798"),
            (r'verify\s*=\s*False', "SSL Verification Disabled", "Medium", "CWE-295"),
            (r'DEBUG\s*=\s*True', "Debug Mode Enabled", "Low", "CWE-489"),
        ]

        for f in files:
            content = f.get("content", "")
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                for pattern, title, severity, cwe in dangerous_patterns:
                    if re.search(pattern, line, re.I):
                        # Get surrounding context (2 lines before/after)
                        start = max(0, i - 3)
                        end = min(len(lines), i + 2)
                        context = "\n".join(lines[start:end])
                        findings.append({
                            "title": f"{title} in {f['file_path']}",
                            "type": cwe,
                            "severity": severity,
                            "file_path": f["file_path"],
                            "line_start": i,
                            "line_end": i,
                            "code_snippet": context,
                            "description": f"{title} detected at {f['file_path']}:{i} — `{line.strip()}`",
                            "cwe_id": cwe,
                            "confidence": 70,
                            "tool_source": "pattern_analysis",
                        })
        return findings

    def _build_full_code_context(self, files: List[Dict]) -> str:
        """Build full code context with line numbers for AI analysis."""
        parts = []
        for f in files:
            content = f.get("content", "")
            # Add line numbers
            numbered_lines = []
            for i, line in enumerate(content.split("\n"), 1):
                numbered_lines.append(f"{i:4d} | {line}")
            numbered_content = "\n".join(numbered_lines[:500])  # Cap at 500 lines per file
            parts.append(f"=== FILE: {f['file_path']} (Language: {f.get('language', 'unknown')}) ===\n{numbered_content}\n")
        return "\n".join(parts)

    def _map_severity(self, bandit_severity: str) -> str:
        return {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}.get(bandit_severity.upper(), "Medium")

    def _map_confidence(self, bandit_confidence: str) -> int:
        return {"HIGH": 90, "MEDIUM": 70, "LOW": 40}.get(bandit_confidence.upper(), 70)

    def _map_file_path(self, tmp_path: str, files: List[Dict]) -> str:
        basename = os.path.basename(tmp_path)
        for f in files:
            if f["file_path"].endswith(basename):
                return f["file_path"]
        return basename
