from typing import Dict, List, Any

def reduce_alerts(vulnerabilities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reduce alert fatigue by deduplicating, merging, and ranking vulnerabilities."""
    unique_vulns = {}
    
    for vuln in vulnerabilities:
        # Create a unique fingerprint based on title/file/line
        fingerprint = f"{vuln.get('title', '')}::{vuln.get('file', '')}::{vuln.get('line', '')}"
        
        if fingerprint in unique_vulns:
            # Merge if existing, prefer highest severity/confidence
            existing = unique_vulns[fingerprint]
            
            new_score = vuln.get("risk_score", 0)
            old_score = existing.get("risk_score", 0)
            
            if new_score > old_score:
                # Merge logic: if new is higher risk, it overtakes base but preserves description combinations
                combined_desc = existing.get("description", "") + "\n\nAlso found: " + vuln.get("description", "")
                vuln["description"] = combined_desc[:2000] # Limit size
                unique_vulns[fingerprint] = vuln
        else:
            unique_vulns[fingerprint] = vuln
            
    # Rank by business impact / risk score
    ranked_list = list(unique_vulns.values())
    ranked_list.sort(key=lambda x: (x.get("risk_score", 0), x.get("confidence", 0)), reverse=True)
    
    # Assign priority rank
    for idx, vuln in enumerate(ranked_list):
        vuln["priority_rank"] = idx + 1
        
    return ranked_list

def verify_reachability(vulnerabilities: List[Dict[str, Any]], graph_engine: Any) -> List[Dict[str, Any]]:
    """Use graph engine to filter or down-rank unreachable vulnerabilities."""
    if not graph_engine:
        return vulnerabilities
        
    for vuln in vulnerabilities:
        file_node = vuln.get("file", "")
        # Very rough reachability heuristic
        if file_node and graph_engine.graph.has_node(file_node):
             # Just checking if it's connected to anything
             degree = graph_engine.graph.degree(file_node)
             if degree == 0:
                 vuln["risk_score"] = max(0, vuln.get("risk_score", 0) - 20)
                 vuln["why_missed"] = "Downranked due to appearing orphaned/unreachable in dependency graph."
                 
    return vulnerabilities
