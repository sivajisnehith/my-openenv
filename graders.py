from typing import List, Dict, Any
from environment import SIEMEnvironment
from models import ActionType

def clamp_score(score: float) -> float:
    # Scale to be strictly between 0.0 and 1.0 (0.01 to 0.99)
    return max(0.01, min(0.99, score))

def grade_task_1(env: SIEMEnvironment) -> float:
    """Detect Attacker IP - Score 1.0 if attacker IP is blocked."""
    attacker_ip = env.ground_truth.get("attacker_ip")
    if attacker_ip in env.blocked_ips:
        return clamp_score(1.0)
    
    # Partial credit for querying logs
    has_queried = any(a.action_type == ActionType.QUERY_LOGS for a in env.action_history)
    if has_queried:
        return clamp_score(0.3)
    return clamp_score(0.0)

def grade_task_2(env: SIEMEnvironment) -> float:
    """Reconstruct Attack Path - Score 1.0 if target server is isolated."""
    target_server = env.ground_truth.get("target")
    if target_server in env.isolated_servers:
        return clamp_score(1.0)
    
    # Partial credit for blocking attacker IP (even if not the final goal)
    attacker_ip = env.ground_truth.get("attacker_ip")
    if attacker_ip in env.blocked_ips:
        return clamp_score(0.5)
    return clamp_score(0.0)

def grade_task_3(env: SIEMEnvironment) -> float:
    """Stop Data Exfiltration - Score 1.0 if exfil IP is blocked or DB server isolated."""
    exfil_ip = env.ground_truth.get("exfil_ip")
    target_server = env.ground_truth.get("target")
    
    if exfil_ip in env.blocked_ips:
        return clamp_score(1.0)
    if target_server in env.isolated_servers:
        return clamp_score(0.8) # Slightly less than blocking IP since isolation is destructive
    
    return clamp_score(0.0)

GRADERS = {
    "task_1": grade_task_1,
    "task_2": grade_task_2,
    "task_3": grade_task_3
}

def calculate_score(task_id: str, env: SIEMEnvironment) -> float:
    grader = GRADERS.get(task_id)
    if grader:
        return grader(env)
    return clamp_score(0.0)
