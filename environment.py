import datetime
import random
from typing import List, Dict, Any, Tuple
from models import Observation, Action, Reward, LogEntry, Severity, ActionType

class SIEMEnvironment:
    def __init__(self, scenario_id: int = 1):
        self.scenario_id = scenario_id
        self.server_status = {
            "web-server": "running",
            "db-server": "running",
            "auth-server": "running"
        }
        self.blocked_ips = set()
        self.isolated_servers = set()
        self.all_logs: List[LogEntry] = []
        self.current_step = 0
        self.max_steps = 20
        self.ground_truth = self._generate_scenario(scenario_id)
        self.action_history = []

    def _generate_scenario(self, scenario_id: int) -> Dict[str, Any]:
        logs = []
        now = datetime.datetime(2026, 4, 8, 10, 0, 0)
        
        # Helper to add noise
        def add_noise(count: int, start_time: datetime.datetime):
            for i in range(count):
                ts = (start_time + datetime.timedelta(seconds=i*30)).isoformat()
                logs.append(LogEntry(
                    timestamp=ts,
                    source=f"192.168.1.{random.randint(2, 254)}",
                    destination="web-server",
                    service="HTTP",
                    message="GET /index.html 200",
                    severity=Severity.INFO,
                    event_id=len(logs)
                ))

        if scenario_id == 1: # Brute Force
            attacker_ip = "10.0.0.51"
            add_noise(10, now)
            for i in range(5):
                ts = (now + datetime.timedelta(minutes=5, seconds=i)).isoformat()
                logs.append(LogEntry(
                    timestamp=ts,
                    source=attacker_ip,
                    destination="auth-server",
                    service="SSH",
                    message="Failed password for root",
                    severity=Severity.WARNING,
                    event_id=len(logs)
                ))
            logs.append(LogEntry(
                timestamp=(now + datetime.timedelta(minutes=5, seconds=6)).isoformat(),
                source=attacker_ip,
                destination="auth-server",
                service="SSH",
                message="Accepted password for root",
                severity=Severity.CRITICAL,
                event_id=len(logs)
            ))
            add_noise(5, now + datetime.timedelta(minutes=6))
            return {"attacker_ip": attacker_ip, "logs": logs, "target": "auth-server", "type": "brute_force"}

        elif scenario_id == 2: # Privilege Escalation
            attacker_ip = "10.0.0.62"
            add_noise(5, now)
            # Step 1: Normal user login
            logs.append(LogEntry(
                timestamp=(now + datetime.timedelta(minutes=2)).isoformat(),
                source=attacker_ip,
                destination="web-server",
                service="HTTP",
                message="User 'guest' logged in",
                severity=Severity.INFO,
                event_id=len(logs)
            ))
            # Step 2: Exploitation attempt
            logs.append(LogEntry(
                timestamp=(now + datetime.timedelta(minutes=3)).isoformat(),
                source=attacker_ip,
                destination="web-server",
                service="HTTP",
                message="Unexpected input detected in /api/upload: '../etc/passwd'",
                severity=Severity.WARNING,
                event_id=len(logs)
            ))
            # Step 3: Shell access / privilege change
            logs.append(LogEntry(
                timestamp=(now + datetime.timedelta(minutes=4)).isoformat(),
                source="web-server",
                destination="web-server",
                service="SYSTEM",
                message="SUDO: guest : TTY=pts/0 ; PWD=/var/www/html ; USER=root ; COMMAND=/usr/bin/find",
                severity=Severity.CRITICAL,
                event_id=len(logs)
            ))
            add_noise(5, now + datetime.timedelta(minutes=5))
            return {"attacker_ip": attacker_ip, "logs": logs, "target": "web-server", "type": "priv_esc"}

        elif scenario_id == 3: # Data Exfiltration
            attacker_ip = "192.168.5.105"
            exfil_dest = "45.12.34.56"
            add_noise(5, now)
            # Step 1: DB Query
            logs.append(LogEntry(
                timestamp=(now + datetime.timedelta(minutes=10)).isoformat(),
                source="web-server",
                destination="db-server",
                service="SQL",
                message="SELECT * FROM customers_pii",
                severity=Severity.WARNING,
                event_id=len(logs)
            ))
            # Step 2: Large transfer
            logs.append(LogEntry(
                timestamp=(now + datetime.timedelta(minutes=11)).isoformat(),
                source="db-server",
                destination=exfil_dest,
                service="FTP",
                message="Outbound transfer: 5.2GB to 45.12.34.56",
                severity=Severity.CRITICAL,
                event_id=len(logs)
            ))
            add_noise(5, now + datetime.timedelta(minutes=12))
            return {"attacker_ip": attacker_ip, "logs": logs, "target": "db-server", "type": "data_exfil", "exfil_ip": exfil_dest}
        
        return {"logs": [], "attacker_ip": "none"}

    def reset(self) -> Observation:
        self.server_status = {k: "running" for k in self.server_status}
        self.blocked_ips = set()
        self.isolated_servers = set()
        self.current_step = 0
        self.all_logs = sorted(self.ground_truth["logs"], key=lambda x: x.timestamp)
        self.action_history = []
        return self.state()

    def state(self) -> Observation:
        # For simplicity, we expose all logs in the observation, 
        # but in a more complex env we'd filter by time or query.
        return Observation(
            logs=self.all_logs,
            active_alerts=[l.message for l in self.all_logs if l.severity == Severity.CRITICAL],
            system_status={k: "isolated" if k in self.isolated_servers else v for k, v in self.server_status.items()},
            terminal_output=f"Step: {self.current_step}/{self.max_steps}. Blocked IPs: {list(self.blocked_ips)}"
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self.current_step += 1
        reward_val = 0.0
        reason = "Neutral action"
        done = self.current_step >= self.max_steps
        
        self.action_history.append(action)

        if action.action_type == ActionType.QUERY_LOGS:
            # In this simple sim, state() always shows logs, but we reward investigation
            reward_val = 0.2
            reason = "Investigating logs"
            
        elif action.action_type == ActionType.BLOCK_IP:
            ip = action.parameters.get("ip")
            if ip:
                self.blocked_ips.add(ip)
                if ip == self.ground_truth.get("attacker_ip") or ip == self.ground_truth.get("exfil_ip"):
                    reward_val = 0.5
                    reason = "Correctly blocked attacker IP"
                    # If they block the right IP, we can consider the attack stopped if Task 3
                else:
                    reward_val = -0.5
                    reason = "Blocked incorrect IP"

        elif action.action_type == ActionType.ISOLATE_SERVER:
            server = action.parameters.get("server")
            if server in self.server_status:
                self.isolated_servers.add(server)
                if server == self.ground_truth.get("target"):
                    reward_val = 0.3
                    reason = "Isolated compromised server"
                else:
                    reward_val = -0.7
                    reason = "Destructive action on healthy server"

        elif action.action_type == ActionType.MARK_SAFE:
            reward_val = 0.0
            reason = "Marked as safe"

        return self.state(), reward_val, done, {"reason": reason}
