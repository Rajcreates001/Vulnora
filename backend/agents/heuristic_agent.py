import logging
from typing import Dict, Any

from db.supabase_client import store_agent_log
from models.schemas import AgentState
from analysis.heuristics.engine import evaluate_findings

logger = logging.getLogger(__name__)

class HeuristicAgent:
    """Layer 4: Heuristic Risk Engine."""
    
    async def run(self, state: AgentState) -> Dict[str, Any]:
        project_id = state.get("project_id", "")
        await store_agent_log(project_id, "heuristic_agent", "Applying deterministic risk overlays based on path and severity.")
        
        try:
            from analysis.heuristics.engine import evaluate_findings
            
            vulns = state.get("vulnerabilities", [])
            ast_data = state.get("ast_data", [])
            graph_data = state.get("graph_data", {})
            
            scored_vulns = evaluate_findings(vulns, ast_data, graph_data)
            
            await store_agent_log(
                project_id, 
                "heuristic_agent", 
                f"Heuristic scoring complete: Assessed risk levels for {len(scored_vulns)} identified findings."
            )
            
            return {
                "vulnerabilities": scored_vulns,
                "current_agent": "heuristic_agent"
            }
        except Exception as e:
            logger.error(f"Heuristic agent failed: {e}")
            await store_agent_log(project_id, "heuristic_agent", f"Error: {str(e)}", log_type="error")
            return {"errors": state.get("errors", []) + [str(e)]}
