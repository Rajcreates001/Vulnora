"""Recon Agent — Analyzes project structure and identifies entry points, APIs, sensitive components."""

import json
from typing import Any, Dict

from agents.base_agent import BaseAgent
from utils.llm_client import get_llm_response
from utils.code_parser import parse_code_structure
from db.redis_client import update_scan_progress

SYSTEM_PROMPT = """You are a senior security reconnaissance specialist. Your task is to analyze a software project's structure and identify:

1. **Entry Points**: HTTP routes, API endpoints, CLI handlers, main functions
2. **Sensitive Components**: Authentication logic, authorization checks, session management
3. **Data Stores**: Database connections, file I/O, cache usage
4. **Configuration Files**: Environment configs, secrets files, deployment manifests
5. **Third-Party Dependencies**: External libraries that could introduce vulnerabilities
6. **Attack Surface**: Public-facing interfaces, user input handling, file uploads

Be thorough and systematic. Output valid JSON with the following structure:
{
    "entry_points": [{"file": "...", "line": N, "type": "...", "description": "..."}],
    "sensitive_components": [{"file": "...", "line": N, "type": "...", "description": "..."}],
    "data_stores": [{"file": "...", "type": "...", "description": "..."}],
    "config_files": [{"file": "...", "risk_level": "...", "description": "..."}],
    "dependencies": [{"name": "...", "risk_notes": "..."}],
    "attack_surface_summary": "...",
    "technology_stack": ["..."],
    "risk_areas": ["..."]
}"""


class ReconAgent(BaseAgent):
    name = "recon_agent"
    description = "Analyzes project structure and identifies entry points and attack surface"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        project_id = state["project_id"]
        files = state.get("files", [])

        await self.log(project_id, f"Starting reconnaissance on {len(files)} files")
        await update_scan_progress(project_id, "recon", self.name, 0.1, "Analyzing project structure...")

        # Parse all files for structural information
        file_structures = []
        file_summaries = []
        for f in files:
            structure = parse_code_structure(f.get("content", ""), f.get("language", "unknown"))
            file_structures.append({"file": f["file_path"], "language": f.get("language"), "structure": structure})
            # Create summary for LLM (limit content length)
            content_preview = f.get("content", "")[:2000]
            file_summaries.append(f"--- {f['file_path']} ({f.get('language', 'unknown')}) ---\n{content_preview}")

        await update_scan_progress(project_id, "recon", self.name, 0.4, "Parsing complete, analyzing with AI...")

        # Send to LLM for deep analysis
        project_overview = "\n\n".join(file_summaries[:30])  # Limit to 30 files for context
        
        user_prompt = f"""Analyze this project and identify all security-relevant components:

FILE STRUCTURE AND CODE:
{project_overview}

PARSED STRUCTURES:
{json.dumps(file_structures[:20], indent=2, default=str)}

Provide a comprehensive security reconnaissance report in JSON format."""

        try:
            response = await get_llm_response(SYSTEM_PROMPT, user_prompt, json_mode=True)
            recon_results = json.loads(response)
        except (json.JSONDecodeError, Exception) as e:
            # await self.log(project_id, f"LLM analysis fallback: {str(e)}", "warning")
            recon_results = self._fallback_analysis(file_structures)

        recon_results["file_structures"] = file_structures

        await self.save_output(project_id, recon_results)
        await self.log(
            project_id,
            f"Recon complete: {len(recon_results.get('entry_points', []))} entry points, "
            f"{len(recon_results.get('sensitive_components', []))} sensitive components found",
            "success",
            {"summary": recon_results.get("attack_surface_summary", "")},
        )
        await update_scan_progress(project_id, "recon", self.name, 1.0, "Reconnaissance complete")

        state["recon_results"] = recon_results
        return state

    def _fallback_analysis(self, file_structures):
        """Fallback analysis using parsed structures only."""
        entry_points = []
        sensitive = []
        for fs in file_structures:
            for route in fs["structure"].get("routes", []):
                entry_points.append({"file": fs["file"], "line": route["line"], "type": "route", "description": route.get("path", "")})
            for auth in fs["structure"].get("auth_patterns", []):
                sensitive.append({"file": fs["file"], "line": auth["line"], "type": "auth", "description": auth.get("code", "")})
        return {
            "entry_points": entry_points,
            "sensitive_components": sensitive,
            "data_stores": [],
            "config_files": [],
            "dependencies": [],
            "attack_surface_summary": "Automated analysis completed with limited AI capability.",
            "technology_stack": [],
            "risk_areas": [],
        }
