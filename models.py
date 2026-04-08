from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from enum import Enum

class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class LogEntry(BaseModel):
    timestamp: str
    source: str
    destination: Optional[str] = None
    service: str
    message: str
    severity: Severity
    event_id: int

class Observation(BaseModel):
    logs: List[LogEntry] = Field(default_factory=list)
    active_alerts: List[str] = Field(default_factory=list)
    system_status: Dict[str, str] = Field(default_factory=dict)
    terminal_output: str = ""

class ActionType(str, Enum):
    QUERY_LOGS = "query_logs"
    BLOCK_IP = "block_ip"
    ISOLATE_SERVER = "isolate_server"
    MARK_SAFE = "mark_safe"

class Action(BaseModel):
    action_type: ActionType
    parameters: Dict[str, Any] = Field(default_factory=dict)

class Reward(BaseModel):
    value: float
    reason: str
