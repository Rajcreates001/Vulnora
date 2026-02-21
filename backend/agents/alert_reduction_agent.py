import logging
from typing import Dict, Any

from db.supabase_client import store_agent_log
from models.schemas import AgentState
from analysis.heuristics.alert_reducer import reduce_alerts, verify_reachability

logger = logging.getLogger(__name__)

class AlertReductionAgent:
    """Layer 5 Overlays: Minimize Alert Fatigue."""
    
    async def run(self, state: AgentState) -> Dict[str, Any]:
        project_id = state.get("project_id", "")
        await store_agent_log(project_id, "alert_reduction_agent", "Reducing alert fatigue based on graph reachability and risk.")
        
        try:
            vulns = state.get("vulnerabilities", []).copy()
            
            # Use deterministic reducer
            graph_engine = None
            graph_data = state.get("graph_data")
            if graph_data:
                from analysis.graph.engine import DependencyGraph
                from networkx.readwrite import json_graph
                graph_engine = DependencyGraph()
                graph_engine.graph = json_graph.node_link_graph(graph_data)
                
            vulns = verify_reachability(vulns, graph_engine)
            final_vulns = reduce_alerts(vulns)
            
            await store_agent_log(
                project_id, 
                "alert_reduction_agent", 
                f"Alerts minimized from {len(state.get('vulnerabilities', []))} to {len(final_vulns)} actionable findings in prioritized order."
            )
            
            return {
                "vulnerabilities": final_vulns,
                "current_agent": "alert_reduction_agent"
            }
        except Exception as e:
            logger.error(f"Alert reduction agent failed: {e}")
            await store_agent_log(project_id, "alert_reduction_agent", f"Error: {str(e)}", log_type="error")
            return {"errors": state.get("errors", []) + [str(e)]}
