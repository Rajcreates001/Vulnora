"""LangGraph workflow orchestrating the multi-agent security analysis pipeline."""

import asyncio
import traceback
from typing import Any, Dict, TypedDict, Annotated

from agents import (
    ReconAgent,
    StaticAnalysisAgent,
    VulnerabilityDiscoveryAgent,
    ExploitSimulationAgent,
    PatchGenerationAgent,
    RiskPrioritizationAgent,
    SecurityDebateAgent,
    ReportGenerationAgent,
    InsightAgent,
    AlertReductionAgent,
    MissedVulnReasoningAgent,
    ParserAgent,
    GraphAgent,
    HeuristicAgent,
)
# ─── Agent Node Functions ─────────────────────────────

async def insight_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = InsightAgent()
    state["current_agent"] = "insight_agent"
    return await agent.run(state)

async def alert_reduction_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = AlertReductionAgent()
    state["current_agent"] = "alert_reduction_agent"
    return await agent.run(state)

async def missed_vuln_reasoning_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = MissedVulnReasoningAgent()
    state["current_agent"] = "missed_vuln_reasoning_agent"
    return await agent.run(state)

async def parser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ParserAgent()
    state["current_agent"] = "parser_agent"
    return await agent.run(state)

async def graph_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = GraphAgent()
    state["current_agent"] = "graph_agent"
    return await agent.run(state)

async def heuristic_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = HeuristicAgent()
    state["current_agent"] = "heuristic_agent"
    return await agent.run(state)
from db.supabase_client import (
    update_project,
    store_vulnerability,
    store_agent_log,
    get_project_files,
    gen_id,
    now_iso,
)
from db.redis_client import update_scan_progress, set_scan_state, broadcast_agent_chat
from db.vector_store import store_code_embeddings


class ScanState(TypedDict):
    project_id: str
    files: list
    ast_data: list
    graph_data: dict
    recon_results: dict
    static_analysis_results: dict
    vulnerabilities: list
    exploits: list
    patches: list
    risk_scores: list
    debate_results: list
    report: dict
    current_agent: str
    logs: list
    errors: list


# ─── Agent Node Functions ─────────────────────────────

async def recon_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ReconAgent()
    state["current_agent"] = "recon_agent"
    return await agent.run(state)


async def static_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = StaticAnalysisAgent()
    state["current_agent"] = "static_analysis_agent"
    return await agent.run(state)


async def vulnerability_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = VulnerabilityDiscoveryAgent()
    state["current_agent"] = "vulnerability_discovery_agent"
    return await agent.run(state)


async def exploit_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ExploitSimulationAgent()
    state["current_agent"] = "exploit_simulation_agent"
    return await agent.run(state)


async def patch_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = PatchGenerationAgent()
    state["current_agent"] = "patch_generation_agent"
    return await agent.run(state)


async def risk_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = RiskPrioritizationAgent()
    state["current_agent"] = "risk_prioritization_agent"
    return await agent.run(state)


async def debate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = SecurityDebateAgent()
    state["current_agent"] = "security_debate_agent"
    return await agent.run(state)


async def report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = ReportGenerationAgent()
    state["current_agent"] = "report_generation_agent"
    return await agent.run(state)


# ─── Main Workflow Runner ─────────────────────────────

async def run_security_scan(project_id: str) -> Dict[str, Any]:
    """Execute the full multi-agent security scan pipeline.
    
    Pipeline: Recon → Static Analysis → Vulnerability → Exploit → Patch → Risk → Debate → Report
    """
    # Initialize state
    state: Dict[str, Any] = {
        "project_id": project_id,
        "files": [],
        "ast_data": [],
        "graph_data": {},
        "recon_results": {},
        "static_analysis_results": {},
        "vulnerabilities": [],
        "exploits": [],
        "patches": [],
        "risk_scores": [],
        "debate_results": [],
        "report": {},
        "current_agent": "",
        "logs": [],
        "errors": [],
    }

    try:
        # Load project files
        await update_project(project_id, {"scan_status": "recon"})
        await set_scan_state(project_id, {"status": "recon", "progress": 0, "agents_completed": []})

        files = await get_project_files(project_id)
        state["files"] = [
            {
                "file_path": f["file_path"],
                "content": f.get("content", ""),
                "language": f.get("language", "unknown"),
            }
            for f in files
        ]

        if not state["files"]:
            await store_agent_log(project_id, "system", "No files found in project", "error")
            await update_project(project_id, {"scan_status": "failed"})
            return {"error": "No files found in project"}

        # Store code embeddings for vector search
        try:
            docs = [f["content"][:1000] for f in state["files"]]
            metas = [{"file_path": f["file_path"], "language": f["language"]} for f in state["files"]]
            ids = [f"file_{i}" for i in range(len(state["files"]))]
            await store_code_embeddings(project_id, docs, metas, ids)
        except Exception as e:
            await store_agent_log(project_id, "system", f"Vector store warning: {str(e)}", "warning")

        # Execute pipeline in sequence
        pipeline = [
            ("recon", recon_node, "recon_agent", "I'm mapping the project structure, entry points, and attack surface."),
            ("analysis", parser_node, "parser_agent", "Layer 1: Parsing codebase into AST for deterministic analysis."),
            ("analysis", static_analysis_node, "static_analysis_agent", "Layer 2: Running local Static Analysis tools."),
            ("analysis", graph_node, "graph_agent", "Layer 3: Building dependency graph from AST."),
            ("analysis", heuristic_node, "heuristic_agent", "Layer 4: Applying heuristic risk scoring on initial findings."),
            ("analysis", vulnerability_node, "vulnerability_discovery_agent", "Layer 5: AI-driven deep-dive to find complex logic flaws."),
            ("exploit", exploit_node, "exploit_simulation_agent", "Generating proof-of-exploit scripts for confirmed vulns."),
            ("patch", patch_node, "patch_generation_agent", "Writing production-ready patches for each vulnerability."),
            ("analysis", risk_node, "risk_prioritization_agent", "Computing CVSS-like risk scores for all findings."),
            ("analysis", insight_node, "insight_agent", "Generating human-level insights and context for each vulnerability."),
            ("analysis", alert_reduction_node, "alert_reduction_agent", "Deduplicating, grouping, and prioritizing vulnerabilities to reduce alert fatigue."),
            ("analysis", missed_vuln_reasoning_node, "missed_vuln_reasoning_agent", "Analyzing why standard tools might have missed these specific vulnerabilities."),
            ("analysis", debate_node, "security_debate_agent", "Verifying and debating findings to eliminate false positives."),
            ("report", report_node, "report_generation_agent", "Compiling the final hybrid security assessment report."),
        ]

        for idx, (stage, node_fn, agent_name, intro_msg) in enumerate(pipeline):
            try:
                await update_project(project_id, {"scan_status": stage})
                progress = idx / len(pipeline)
                await update_scan_progress(
                    project_id, stage, agent_name, progress,
                    f"Running {agent_name.replace('_', ' ').title()}..."
                )
                await broadcast_agent_chat(project_id, agent_name, intro_msg, "info")
                
                result_state = await node_fn(state)
                if result_state:
                    state.update(result_state)
                    
                # Mark this agent as completed in scan progress
                done_progress = (idx + 1) / len(pipeline)
                await update_scan_progress(
                    project_id, stage, agent_name, done_progress,
                    f"{agent_name.replace('_', ' ').title()} completed.",
                    mark_agent_completed=True,
                )
                await broadcast_agent_chat(
                    project_id, agent_name,
                    f"Finished my analysis. Passing results to the next agent.",
                    "success",
                )
            except Exception as e:
                error_msg = f"Error in {node_fn.__name__}: {str(e)}"
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(error_msg)
                await store_agent_log(project_id, "system", error_msg, "error")
                await broadcast_agent_chat(project_id, agent_name, f"Hit an error: {str(e)}", "error")
                # Still mark progress so it moves forward
                done_progress = (idx + 1) / len(pipeline)
                await update_scan_progress(
                    project_id, stage, agent_name, done_progress,
                    f"{agent_name} encountered an error, continuing...",
                    mark_agent_completed=True,
                )
                # Continue pipeline despite individual agent failures
                continue
            finally:
                # Small delay between agents to avoid rate limiting on LLM providers
                await asyncio.sleep(1)

        # Store vulnerabilities in database
        vulns = state.get("vulnerabilities", [])
        exploits = state.get("exploits", [])
        patches = state.get("patches", [])

        # Build maps for merging
        exploit_map = {e.get("vulnerability_title", ""): e for e in exploits}
        patch_map = {p.get("vulnerability_title", ""): p for p in patches}

        for v in vulns:
            title = v.get("title", "")
            exploit_data = exploit_map.get(title, {})
            patch_data = patch_map.get(title, {})

            vuln_record = {
                "id": gen_id(),
                "project_id": project_id,
                "title": title,
                "vulnerability_type": v.get("vulnerability_type", "Unknown"),
                "severity": v.get("severity", "Medium"),
                "description": v.get("description", ""),
                "file_path": v.get("file_path", ""),
                "line_start": v.get("line_start", 0),
                "line_end": v.get("line_end", 0),
                "vulnerable_code": v.get("vulnerable_code", ""),
                "exploit": exploit_data.get("impact_description", ""),
                "exploit_script": exploit_data.get("proof_of_exploit", ""),
                "patch": patch_data.get("patched_code", ""),
                "patch_explanation": patch_data.get("explanation", ""),
                "risk_score": v.get("risk_score", 50),
                "confidence": v.get("confidence", 50),
                "exploitability": v.get("exploitability", 50),
                "impact": v.get("impact", 50),
                "cwe_id": v.get("cwe_id", ""),
                "cvss_vector": v.get("cvss_vector", ""),
                "attack_path": exploit_data.get("attack_path", []),
                "created_at": now_iso(),
            }
            await store_vulnerability(vuln_record)

        # Mark scan as completed
        await update_project(project_id, {"scan_status": "completed"})
        await update_scan_progress(project_id, "completed", "", 1.0, "Scan complete!")
        await store_agent_log(
            project_id, "system",
            f"Scan completed. Found {len(vulns)} vulnerabilities.",
            "success",
        )

        return state.get("report", {})

    except Exception as e:
        error_msg = f"Scan failed: {str(e)}\n{traceback.format_exc()}"
        await store_agent_log(project_id, "system", error_msg, "error")
        await update_project(project_id, {"scan_status": "failed"})
        await update_scan_progress(project_id, "failed", "", 0, error_msg)
        return {"error": error_msg}
