import networkx as nx
from typing import Dict, List, Any

class DependencyGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        
    def build_from_ast(self, ast_data: List[Dict[str, Any]]):
        """Construct a lightweight dependency graph from AST parsed files."""
        for file_data in ast_data:
            filename = file_data.get("filename")
            self.graph.add_node(filename, type="file", lang=file_data.get("language"))
            
            for func in file_data.get("functions", []):
                func_name = func.get("name")
                if not func_name:
                     continue
                     
                node_id = f"{filename}::{func_name}"
                self.graph.add_node(node_id, type="function", file=filename)
                self.graph.add_edge(filename, node_id, relationship="defines")
                
                # In a full AST parser, we would analyze the function body for calls.
                # Here we are just building the skeleton from the available AST definition nodes.

    def find_paths(self, source: str, sink: str) -> List[List[str]]:
        """Find reachability paths from source identifier to sink identifier."""
        try:
             # Basic shortest path
             if self.graph.has_node(source) and self.graph.has_node(sink):
                 return list(nx.all_shortest_paths(self.graph, source=source, target=sink))
        except Exception:
             pass
        return []

    def reachable(self, node: str) -> bool:
         """Check if a node has any incoming paths (rudimentary)."""
         if self.graph.has_node(node):
              return self.graph.in_degree(node) > 0
         return False
         
    def to_dict(self) -> Dict[str, Any]:
         from networkx.readwrite import json_graph
         return json_graph.node_link_data(self.graph)

def generate_graph(ast_data: List[Dict[str, Any]]) -> DependencyGraph:
    engine = DependencyGraph()
    engine.build_from_ast(ast_data)
    return engine
