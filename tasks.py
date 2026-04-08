from typing import List, Dict, Any
from pydantic import BaseModel

class Task(BaseModel):
    id: str
    name: str
    description: str
    scenario_id: int

TASKS = [
    Task(
        id="task_1",
        name="Detect Attacker IP",
        description="Analyze logs to identify the IP address responsible for the brute force attack on the auth-server.",
        scenario_id=1
    ),
    Task(
        id="task_2",
        name="Reconstruct Attack Path",
        description="Identify the sequence of events and the compromised server in the privilege escalation scenario.",
        scenario_id=2
    ),
    Task(
        id="task_3",
        name="Stop Data Exfiltration",
        description="Identify the data exfiltration attempt and take the correct action (block IP or isolate server) to stop it.",
        scenario_id=3
    )
]
