"""Unified LangGraph workflows for Verdexa platform.

Contains both:
  1. Security Scan Pipeline  — multi-agent vulnerability analysis
  2. Hiring Panel Pipeline   — multi-agent candidate evaluation
"""

import asyncio
import traceback
from typing import Any, Dict, TypedDict
from langgraph.graph import StateGraph, END

# ════════════════════════════════════════════════════════════════
# SECURITY SCAN WORKFLOW
# ════════════════════════════════════════════════════════════════

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
from db.supabase_client import (
    update_project,
    store_vulnerability,
    store_agent_log,
    get_project_files,
    delete_vulnerabilities_by_project,
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


# ─── Security Agent Node Functions ────────────────────────

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


# ─── Main Security Scan Runner ────────────────────────────

async def run_security_scan(project_id: str) -> Dict[str, Any]:
    """Execute the full multi-agent security scan pipeline.

    Pipeline: Recon → Static Analysis → Vulnerability → Exploit → Patch → Risk → Debate → Report
    """
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
        print(f"[SCAN] {project_id}: Initializing scan workflow...")
        import sys
        sys.stdout.flush()
        
        await update_project(project_id, {"scan_status": "recon"})
        await set_scan_state(project_id, {"status": "recon", "progress": 0, "agents_completed": []})
        await store_agent_log(project_id, "system", "Security scan workflow started", "info")
        await broadcast_agent_chat(project_id, "system", "Security scan workflow started", "info")
        
        # Delete old vulnerabilities (non-blocking)
        try:
            await delete_vulnerabilities_by_project(project_id)
        except Exception as e:
            print(f"[SCAN] {project_id}: Warning - failed to delete old vulnerabilities: {e}")

        try:
            files = await get_project_files(project_id)
        except Exception as e:
            print(f"[SCAN] {project_id}: get_project_files failed: {e}")
            files = []
        
        print(f"[SCAN] {project_id}: Loaded {len(files)} files from database")
        sys.stdout.flush()
        
        state["files"] = [
            {
                "file_path": f.get("file_path", ""),
                "content": f.get("content", "") or "",
                "language": f.get("language", "unknown"),
            }
            for f in files
        ]

        # If no files, inject a minimal sample so the pipeline runs and user sees agents/logs
        if not state["files"]:
            sample_content = '''# Sample application (no files were uploaded - running demo scan)
def login(username, password):
    query = "SELECT * FROM users WHERE user=%s AND pass=%s" % (username, password)
    return db.execute(query)

@app.route("/search")
def search():
    q = request.args.get("q", "")
    return render_template("search.html", results=db.search(q))
'''
            state["files"] = [
                {
                    "file_path": "sample_app.py",
                    "content": sample_content,
                    "language": "python",
                }
            ]
            msg = "No files in project. Running scan with sample file so you can see agent output."
            print(f"[SCAN] {project_id}: {msg}")
            await store_agent_log(project_id, "system", msg, "info")
            await broadcast_agent_chat(project_id, "system", msg, "info")

        # Store code embeddings (non-blocking, skip if slow)
        try:
            docs = [f["content"][:500] for f in state["files"][:20]]
            metas = [{"file_path": f["file_path"], "language": f["language"]} for f in state["files"][:20]]
            ids = [f"file_{i}" for i in range(len(docs))]
            await asyncio.wait_for(store_code_embeddings(project_id, docs, metas, ids), timeout=5)
            print(f"[SCAN] {project_id}: Stored code embeddings")
        except Exception as e:
            print(f"[SCAN] {project_id}: Skipped embeddings (non-critical): {e}")
            pass

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
                print(f"[SCAN] {project_id}: Starting {agent_name} ({idx+1}/{len(pipeline)})")
                import sys
                sys.stdout.flush()
                
                await update_project(project_id, {"scan_status": stage})
                progress = idx / len(pipeline)
                await update_scan_progress(
                    project_id, stage, agent_name, progress,
                    f"Running {agent_name.replace('_', ' ').title()}..."
                )
                # Broadcast intro message - ensure it's sent
                try:
                    await broadcast_agent_chat(project_id, agent_name, intro_msg, "info")
                except Exception as broadcast_err:
                    print(f"[SCAN] {project_id}: Failed to broadcast chat for {agent_name}: {broadcast_err}")
                
                # Log agent start
                try:
                    await store_agent_log(project_id, agent_name, intro_msg, "info")
                except Exception as log_err:
                    print(f"[SCAN] {project_id}: Failed to log for {agent_name}: {log_err}")

                # Execute agent with timeout to prevent hanging
                try:
                    result_state = await asyncio.wait_for(node_fn(state), timeout=300.0)  # 5 min timeout per agent
                    if result_state:
                        state.update(result_state)
                    print(f"[SCAN] {project_id}: Completed {agent_name}")
                    import sys
                    sys.stdout.flush()
                except asyncio.TimeoutError:
                    error_msg = f"Agent {agent_name} timed out after 5 minutes"
                    print(f"[SCAN] {project_id}: {error_msg}")
                    await store_agent_log(project_id, "system", error_msg, "error")
                    await broadcast_agent_chat(project_id, agent_name, error_msg, "error")
                    # Continue to next agent
                    result_state = None

                # After vulnerability discovery, persist to DB so /api/results returns data during scan
                if agent_name == "vulnerability_discovery_agent":
                    for v in state.get("vulnerabilities", []):
                        if not v.get("title"):
                            continue
                        confidence_val = v.get("confidence", 50)
                        if isinstance(confidence_val, str):
                            try: confidence_val = int(confidence_val)
                            except ValueError: confidence_val = 50
                        risk_score_val = v.get("risk_score", 50)
                        if isinstance(risk_score_val, str):
                            try: risk_score_val = int(risk_score_val)
                            except ValueError: risk_score_val = 50
                        vuln_record = {
                            "id": gen_id(),
                            "project_id": project_id,
                            "title": v.get("title", "")[:255],
                            "vulnerability_type": v.get("vulnerability_type", "Unknown")[:100],
                            "severity": v.get("severity", "Medium")[:20],
                            "description": v.get("description", ""),
                            "file_path": v.get("file_path", ""),
                            "line_start": v.get("line_start", 0),
                            "line_end": v.get("line_end", 0),
                            "vulnerable_code": v.get("vulnerable_code", ""),
                            "exploit": "",
                            "exploit_script": "",
                            "patch": "",
                            "patch_explanation": "",
                            "risk_score": max(0, min(100, int(risk_score_val))),
                            "confidence": max(0, min(100, int(confidence_val))),
                            "exploitability": 50,
                            "impact": 50,
                            "cwe_id": v.get("cwe_id", "")[:50],
                            "cvss_vector": v.get("cvss_vector", "")[:50],
                            "attack_path": [],
                            "created_at": now_iso(),
                        }
                        try:
                            await store_vulnerability(vuln_record)
                            print(f"[SCAN] {project_id}: Stored vulnerability: {v.get('title', 'Unknown')[:50]}")
                        except Exception as e:
                            error_msg = f"Failed to store vulnerability '{v.get('title', 'Unknown')}': {str(e)}"
                            print(f"ERROR storing vulnerability: {error_msg}")
                            await store_agent_log(project_id, "system", error_msg, "error")

                done_progress = (idx + 1) / len(pipeline)
                await update_scan_progress(
                    project_id, stage, agent_name, done_progress,
                    f"{agent_name.replace('_', ' ').title()} completed.",
                    mark_agent_completed=True,
                )
                # Broadcast completion message
                try:
                    await broadcast_agent_chat(
                        project_id, agent_name,
                        f"Finished my analysis. Passing results to the next agent.",
                        "success",
                    )
                except Exception as broadcast_err:
                    print(f"[SCAN] {project_id}: Failed to broadcast completion for {agent_name}: {broadcast_err}")
            except Exception as e:
                error_msg = f"Error in {node_fn.__name__}: {str(e)}\n{traceback.format_exc()}"
                print(f"ERROR in {agent_name} for {project_id}: {error_msg}")  # Debug log
                import sys
                sys.stderr.write(f"ERROR in {agent_name} for {project_id}: {error_msg}\n")
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(error_msg)
                try:
                    await store_agent_log(project_id, "system", error_msg, "error")
                    await broadcast_agent_chat(project_id, agent_name, f"Hit an error: {str(e)}", "error")
                except Exception as log_error:
                    print(f"[SCAN] {project_id}: Failed to log error: {log_error}")
                    # Try to log to console at least
                    import sys
                    sys.stderr.write(f"ERROR LOGGING FAILED: {log_error}\n")
                done_progress = (idx + 1) / len(pipeline)
                try:
                    await update_scan_progress(
                        project_id, stage, agent_name, done_progress,
                        f"{agent_name} encountered an error, continuing...",
                        mark_agent_completed=True,
                    )
                except Exception as progress_error:
                    print(f"Failed to update progress: {progress_error}")
                # Continue to next agent instead of stopping
                continue
            finally:
                pass

        # Replace with full vulnerability records (exploit, patch, risk, etc.)
        # Only delete if we have new vulnerabilities to store
        vulns = state.get("vulnerabilities", [])
        if vulns:
            print(f"[SCAN] {project_id}: Preparing to store {len(vulns)} vulnerabilities")
            await delete_vulnerabilities_by_project(project_id)
        else:
            print(f"[SCAN] {project_id}: WARNING - No vulnerabilities found in state")
        exploits = state.get("exploits", [])
        patches = state.get("patches", [])

        exploit_map = {e.get("vulnerability_title", ""): e for e in exploits}
        patch_map = {p.get("vulnerability_title", ""): p for p in patches}

        successfully_stored = 0
        for v in vulns:
            title = v.get("title", "")
            if not title:
                continue

            exploit_data = exploit_map.get(title, {})
            patch_data = patch_map.get(title, {})

            # Ensure safe confidence math to avoid out-of-bounds DB integers
            confidence_val = v.get("confidence", 50)
            if isinstance(confidence_val, str):
                try: confidence_val = int(confidence_val)
                except ValueError: confidence_val = 50
            
            risk_score_val = v.get("risk_score", 50)
            if isinstance(risk_score_val, str):
                try: risk_score_val = int(risk_score_val)
                except ValueError: risk_score_val = 50

            vuln_record = {
                "id": gen_id(),
                "project_id": project_id,
                "title": title[:255], # Ensure title doesn't exceed varchar limits
                "vulnerability_type": v.get("vulnerability_type", "Unknown")[:100],
                "severity": v.get("severity", "Medium")[:20],
                "description": v.get("description", ""),
                "file_path": v.get("file_path", ""),
                "line_start": v.get("line_start", 0),
                "line_end": v.get("line_end", 0),
                "vulnerable_code": v.get("vulnerable_code", ""),
                "exploit": exploit_data.get("impact_description", ""),
                "exploit_script": exploit_data.get("proof_of_exploit", ""),
                "patch": patch_data.get("patched_code", ""),
                "patch_explanation": patch_data.get("explanation", ""),
                "risk_score": max(0, min(100, int(risk_score_val))),
                "confidence": max(0, min(100, int(confidence_val))),
                "exploitability": 50, # Defaults
                "impact": 50, # Defaults
                "cwe_id": v.get("cwe_id", "")[:50],
                "cvss_vector": v.get("cvss_vector", "")[:50],
                "attack_path": exploit_data.get("attack_path", []),
                "created_at": now_iso(),
            }
            try:
                await store_vulnerability(vuln_record)
                successfully_stored += 1
                if successfully_stored % 10 == 0:
                    print(f"[SCAN] {project_id}: Stored {successfully_stored} vulnerabilities so far...")
            except Exception as e:
                db_err_msg = f"Failed to store vulnerability '{title}': {str(e)}"
                print(f"ERROR storing vulnerability '{title}': {e}")
                try:
                    await store_agent_log(project_id, "system", db_err_msg, "error")
                except Exception:
                    pass  # Don't fail scan if logging fails

        # Mark scan as completed
        await update_project(project_id, {"scan_status": "completed"})
        await update_scan_progress(project_id, "completed", "", 1.0, "Scan complete!")
        await set_scan_state(project_id, {
            "status": "completed",
            "current_agent": "",
            "progress": 1.0,
            "agents_completed": [p[2] for p in pipeline],  # All agents completed
            "message": f"Scan completed. Successfully stored {successfully_stored}/{len(vulns)} vulnerabilities.",
        })
        await store_agent_log(
            project_id, "system",
            f"Scan completed. Successfully stored {successfully_stored}/{len(vulns)} vulnerabilities.",
            "success",
        )
        print(f"[SCAN] {project_id}: Scan completed successfully. Stored {successfully_stored}/{len(vulns)} vulnerabilities.")
        import sys
        sys.stdout.flush()

        return state.get("report", {})

    except Exception as e:
        error_msg = f"Scan pipeline crashed: {str(e)}\n{traceback.format_exc()}"
        print(f"ERROR in run_security_scan for {project_id}: {error_msg}")  # Console log for debugging
        await store_agent_log(project_id, "system", error_msg, "error")
        await update_project(project_id, {"scan_status": "failed"})
        await update_scan_progress(project_id, "failed", "", 0, error_msg)
        await set_scan_state(project_id, {
            "status": "failed",
            "current_agent": "",
            "progress": 0,
            "agents_completed": [],
            "message": error_msg,
        })
        return {"error": error_msg}


# ════════════════════════════════════════════════════════════════
# HIRING PANEL WORKFLOW
# ════════════════════════════════════════════════════════════════

from agents import (
    ResumeAnalystAgent,
    TechnicalDepthAgent,
    BehavioralPsychologistAgent,
    DomainExpertAgent,
    HiringManagerAgent,
    ContradictionDetectorAgent,
    BiasAuditorAgent,
    ConsensusNegotiatorAgent,
)


class HiringState(TypedDict):
    """State that flows through the hiring panel graph."""
    resume_text: str
    transcript_text: str
    job_description: str
    candidate_id: str
    agent_analyses: Dict[str, str]
    agent_logs: list
    resume_analysis: Dict[str, Any]
    technical_analysis: Dict[str, Any]
    behavioral_analysis: Dict[str, Any]
    domain_analysis: Dict[str, Any]
    hiring_manager_analysis: Dict[str, Any]
    contradiction_analysis: Dict[str, Any]
    bias_audit: Dict[str, Any]
    consensus: Dict[str, Any]


# Initialize agent instances
resume_agent = ResumeAnalystAgent()
technical_agent = TechnicalDepthAgent()
behavioral_agent = BehavioralPsychologistAgent()
domain_agent = DomainExpertAgent()
hiring_manager_agent = HiringManagerAgent()
contradiction_agent = ContradictionDetectorAgent()
bias_agent = BiasAuditorAgent()
consensus_agent = ConsensusNegotiatorAgent()


# ─── Hiring Node Functions ────────────────────────────────

async def input_node(state: HiringState) -> HiringState:
    """Initialize the state with defaults."""
    state.setdefault("agent_analyses", {})
    state.setdefault("agent_logs", [])
    state.setdefault("resume_analysis", {})
    state.setdefault("technical_analysis", {})
    state.setdefault("behavioral_analysis", {})
    state.setdefault("domain_analysis", {})
    state.setdefault("hiring_manager_analysis", {})
    state.setdefault("contradiction_analysis", {})
    state.setdefault("bias_audit", {})
    state.setdefault("consensus", {})
    return state


async def resume_analysis_node(state: HiringState) -> HiringState:
    return await resume_agent.invoke(state)


async def technical_analysis_node(state: HiringState) -> HiringState:
    return await technical_agent.invoke(state)


async def behavioral_analysis_node(state: HiringState) -> HiringState:
    return await behavioral_agent.invoke(state)


async def domain_analysis_node(state: HiringState) -> HiringState:
    return await domain_agent.invoke(state)


async def contradiction_detection_node(state: HiringState) -> HiringState:
    return await contradiction_agent.invoke(state)


async def hiring_manager_node(state: HiringState) -> HiringState:
    return await hiring_manager_agent.invoke(state)


async def bias_audit_node(state: HiringState) -> HiringState:
    return await bias_agent.invoke(state)


async def consensus_node(state: HiringState) -> HiringState:
    return await consensus_agent.invoke(state)


async def final_report_node(state: HiringState) -> HiringState:
    """Compile the final report from all analyses."""
    consensus = state.get("consensus", {})
    state["agent_logs"].append({
        "agent_name": "System",
        "agent_role": "Orchestrator",
        "message": f"Evaluation complete. Final decision: {consensus.get('final_decision', 'Unknown')} "
                   f"with {consensus.get('confidence', 0)}% confidence.",
        "phase": "final",
    })
    return state


# ─── Build Hiring Graph ──────────────────────────────────

def build_hiring_graph() -> StateGraph:
    """Construct the LangGraph workflow for the hiring panel."""
    workflow = StateGraph(HiringState)

    workflow.add_node("input", input_node)
    workflow.add_node("resume_analysis", resume_analysis_node)
    workflow.add_node("technical_analysis", technical_analysis_node)
    workflow.add_node("behavioral_analysis", behavioral_analysis_node)
    workflow.add_node("domain_analysis", domain_analysis_node)
    workflow.add_node("contradiction_detection", contradiction_detection_node)
    workflow.add_node("hiring_manager", hiring_manager_node)
    workflow.add_node("bias_audit", bias_audit_node)
    workflow.add_node("consensus", consensus_node)
    workflow.add_node("final_report", final_report_node)

    workflow.set_entry_point("input")
    workflow.add_edge("input", "resume_analysis")
    workflow.add_edge("resume_analysis", "technical_analysis")
    workflow.add_edge("technical_analysis", "behavioral_analysis")
    workflow.add_edge("behavioral_analysis", "domain_analysis")
    workflow.add_edge("domain_analysis", "contradiction_detection")
    workflow.add_edge("contradiction_detection", "hiring_manager")
    workflow.add_edge("hiring_manager", "bias_audit")
    workflow.add_edge("bias_audit", "consensus")
    workflow.add_edge("consensus", "final_report")
    workflow.add_edge("final_report", END)

    return workflow.compile()


# Compiled graph singleton
hiring_graph = build_hiring_graph()
