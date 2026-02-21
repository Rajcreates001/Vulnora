import logging
from typing import Dict, Any

from db.supabase_client import store_agent_log
from models.schemas import AgentState
from analysis.parser.engine import collect_ast_data

logger = logging.getLogger(__name__)

class ParserAgent:
    """Layer 1: Deterministic AST Code Parsing."""
    
    async def run(self, state: AgentState) -> Dict[str, Any]:
        project_id = state.get("project_id", "")
        await store_agent_log(project_id, "parser_agent", "Initializing AST syntax tree parser for deterministic layer 1.")
        
        try:
            from config import settings
            import os
            project_dir = os.path.join(settings.upload_dir, project_id)
            
            from analysis.parser.engine import collect_ast_data
            import asyncio
            ast_data = await asyncio.to_thread(collect_ast_data, project_dir)
            
            await store_agent_log(
                project_id, 
                "parser_agent", 
                f"AST Parsing complete: Generated structures for {len(ast_data)} files."
            )
            
            return {
                "ast_data": ast_data,
                "current_agent": "parser_agent"
            }
        except Exception as e:
            logger.error(f"Parser agent failed: {e}")
            await store_agent_log(project_id, "parser_agent", f"Error: {str(e)}", log_type="error")
            return {"errors": state.get("errors", []) + [str(e)]}
