"""Patch Generation Agent — Generates secure code fixes with explanations."""

import json
from typing import Any, Dict, List

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from db.redis_client import update_scan_progress

SYSTEM_PROMPT = """You are a senior secure software engineer. Given vulnerability details and the surrounding code, generate:

1. A secure patch that fixes the vulnerability
2. A clear explanation of what was wrong and how the fix works
3. Any additional security recommendations

Your patches must:
- Be production-ready and correct
- Follow security best practices
- Maintain the original functionality
- Include proper input validation, output encoding, parameterized queries, etc.
- Be minimal — change only what's needed

Output valid JSON:
{
    "patches": [
        {
            "vulnerability_title": "...",
            "file_path": "...",
            "original_code": "the vulnerable code",
            "patched_code": "the fixed code",
            "explanation": "What was wrong and how the fix works",
            "security_notes": ["additional security recommendations"],
            "testing_recommendations": ["how to verify the fix"]
        }
    ]
}"""


class PatchGenerationAgent(BaseAgent):
    name = "patch_generation_agent"
    description = "Generates secure code fixes for discovered vulnerabilities"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        vulns = state.get("vulnerabilities", [])
        files = state.get("files", [])

        if not vulns:
            await self.log(project_id, "No vulnerabilities to generate patches for")
            state["patches"] = []
            return state

        await self.log(project_id, f"Generating patches for {len(vulns)} vulnerabilities")
        await update_scan_progress(project_id, "patch", self.name, 0.1, "Generating security patches...")

        # Build file content map for context
        file_map = {f["file_path"]: f.get("content", "") for f in files}

        # Process vulnerabilities in batches
        all_patches: List[Dict] = []
        batch_size = 5

        for i in range(0, len(vulns), batch_size):
            batch = vulns[i:i + batch_size]
            progress = 0.1 + (0.8 * (i / max(len(vulns), 1)))
            await update_scan_progress(project_id, "patch", self.name, progress, f"Patching batch {i // batch_size + 1}...")

            # Get surrounding code for context
            vuln_context = []
            for v in batch:
                file_content = file_map.get(v.get("file_path", ""), "")
                lines = file_content.split("\n")
                line_start = max(0, v.get("line_start", 1) - 10)
                line_end = min(len(lines), v.get("line_end", 1) + 10)
                surrounding = "\n".join(lines[line_start:line_end])
                vuln_context.append({
                    **v,
                    "surrounding_code": surrounding,
                    "full_file_snippet": file_content[:3000],
                })

            user_prompt = f"""Generate secure patches for these vulnerabilities:

{json.dumps(vuln_context, indent=2, default=str)}

Requirements:
- Each patch must be production-ready
- Maintain original functionality
- Follow security best practices
- Include clear explanations"""

            try:
                response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True, max_tokens=4096)
                batch_results = json.loads(response)
                all_patches.extend(batch_results.get("patches", []))
            except Exception as e:
                await self.log(project_id, f"Patch generation error: {str(e)}", "warning")
                # Generate basic patches as fallback
                for v in batch:
                    all_patches.append(self._basic_patch(v))

        await self.save_output(project_id, {"patches": all_patches})
        await self.log(project_id, f"Patch generation complete: {len(all_patches)} patches", "success")
        await update_scan_progress(project_id, "patch", self.name, 1.0, "Patch generation complete")

        state["patches"] = all_patches
        return state

    def _basic_patch(self, vuln: Dict) -> Dict:
        vuln_type = vuln.get("vulnerability_type", "").lower()
        explanation = "Apply proper input validation and follow security best practices."

        if "sql injection" in vuln_type:
            explanation = "Use parameterized queries instead of string concatenation. Never interpolate user input directly into SQL statements."
        elif "xss" in vuln_type:
            explanation = "Sanitize and encode all user input before rendering in HTML. Use framework-provided escaping functions."
        elif "command injection" in vuln_type:
            explanation = "Avoid using shell=True with subprocess. Use argument lists and validate all input."
        elif "hardcoded" in vuln_type or "secret" in vuln_type:
            explanation = "Move secrets to environment variables or a secret management service."
        elif "deserialization" in vuln_type:
            explanation = "Use safe deserialization methods. For YAML, use yaml.safe_load(). Avoid pickle with untrusted data."

        return {
            "vulnerability_title": vuln.get("title", "Unknown"),
            "file_path": vuln.get("file_path", ""),
            "original_code": vuln.get("vulnerable_code", ""),
            "patched_code": "# See explanation for recommended fix approach",
            "explanation": explanation,
            "security_notes": ["Review the fix thoroughly before deploying"],
            "testing_recommendations": ["Test with malicious input payloads"],
        }
