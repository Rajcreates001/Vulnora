from typing import Dict, List, Any

# Heuristic weights for common vulnerabilities
SINK_WEIGHTS = {
    "sql": 30,
    "system": 35,
    "eval": 40,
    "xss": 25,
    "file": 20
}

SOURCE_WEIGHTS = {
    "request": 20,
    "header": 15,
    "cookie": 15,
    "db": 5
}

def score_vulnerability(vuln: Dict[str, Any], ast_data: List[Dict[str, Any]] = None, graph_data: Any = None) -> Dict[str, Any]:
    """Apply heuristic deterministic rules to calculate risk score and exploit probability."""
    risk_score = 10.0
    exploit_prob = 10.0
    confidence = 50.0
    
    title = vuln.get("title", "").lower()
    desc = vuln.get("description", "").lower()
    
    # Check severity
    base_severity = str(vuln.get("severity", "LOW")).upper()
    if base_severity == "CRITICAL":
        risk_score += 60
    elif base_severity == "HIGH":
        risk_score += 40
    elif base_severity == "MEDIUM":
        risk_score += 20
        
    # Check sinks
    for sink, weight in SINK_WEIGHTS.items():
        if sink in title or sink in desc:
            risk_score += weight
            exploit_prob += weight * 0.8
            confidence += 10
            
    # Check sources
    for source, weight in SOURCE_WEIGHTS.items():
        if source in desc:
            risk_score += weight
            exploit_prob += weight * 0.9
            
    # Simple bounds clamping
    risk_score = min(max(risk_score, 0), 100)
    exploit_prob = min(max(exploit_prob, 0), 100)
    confidence = min(max(confidence, 0), 100)
    
    vuln["risk_score"] = float(round(risk_score, 1))
    vuln["exploit_probability"] = float(round(exploit_prob, 1))
    vuln["confidence"] = float(round(confidence, 1))
    
    return vuln

def evaluate_findings(findings: List[Dict[str, Any]], ast_data: List[Dict[str, Any]] = None, graph_data: Any = None) -> List[Dict[str, Any]]:
    """Heuristically score all findings from static/LLM engines."""
    scored_findings = []
    for f in findings:
        scored = score_vulnerability(f, ast_data, graph_data)
        scored_findings.append(scored)
    return scored_findings
