import logging
from typing import Dict, Any

from db.supabase_client import store_agent_log
from models.schemas import AgentState
from analysis.graph.engine import generate_graph

logger = logging.getLogger(__name__)

class GraphAgent:
    """Layer 3: Dependency Graph Reasoning Engine."""
    
    async def run(self, state: AgentState) -> Dict[str, Any]:
        project_id = state.get("project_id", "")
        await store_agent_log(project_id, "graph_agent", "Building dependency graph from Layer 1 AST Data.")
        
        try:
            from analysis.graph.engine import generate_graph
            
            ast_data = state.get("ast_data", [])
            engine = generate_graph(ast_data)
            
            graph_data = engine.to_dict()
            
            await store_agent_log(
                project_id, 
                "graph_agent", 
                f"Graph reasoning complete: NetworkX structure contains {len(graph_data['nodes'])} connected nodes."
            )
            
            return {
                "graph_data": graph_data,
                "current_agent": "graph_agent"
            }
        except Exception as e:
            logger.error(f"Graph agent failed: {e}")
            await store_agent_log(project_id, "graph_agent", f"Error: {str(e)}", log_type="error")
            return {"errors": state.get("errors", []) + [str(e)]}
