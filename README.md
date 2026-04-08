---
title: SIEM Security OpenEnv
emoji: 🛡️
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
tags:
- openenv
---

# SIEM Security OpenEnv

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-green)](https://github.com/openenv/openenv)

## Motivation

Cybersecurity operations require Level-1 SOC analysts to process thousands of logs daily. Training AI agents to perform this investigation—detecting attackers, reconstructing attack paths, and taking safe remediation actions—is a critical real-world application of agentic AI. 

This environment simulates a corporate SIEM linked to a web server, auth server, and database server. It provides a structured workspace for RL agents to learn defensive security maneuvers.

## Action Space

The agent acts via the following typed actions:

| Action | Description | Parameters |
| :--- | :--- | :--- |
| `query_logs` | Deep dive into the current log buffer. | None |
| `block_ip` | Implement a firewall rule for a specific IP. | `ip`: string |
| `isolate_server` | Disconnect a server from the internal network. | `server`: string |
| `mark_safe` | Close the investigation as a false positive. | None |

## Observation Space

The observation returned at each step contains:

- **`logs`**: A list of structured log entries (Timestamp, Source, Destination, Service, Message, Severity).
- **`active_alerts`**: High-severity alerts extracted automatically by the SIEM logic.
- **`system_status`**: Current operational state of the network (e.g., which servers are isolated).
- **`terminal_output`**: Human-readable status update.

## Tasks & Challenges

| Task ID | Name | Difficulty | Description |
| :--- | :--- | :--- | :--- |
| `task_1` | Detect Attacker IP | Easy | Identify the IP brute-forcing the auth server. |
| `task_2` | Reconstruct Path | Medium | Trace a privilege escalation chain on the web server. |
| `task_3` | Stop Exfiltration | Hard | Neutralize a database dump being sent to a remote C2. |

## Reward System

The reward function provides shaping for partial progress:
- **Investigation (+0.2)**: Granted when the agent queries logs.
- **Precise Remediation (+0.5)**: Granted for blocking the correct attacker IP.
- **Correlative Success (+0.3)**: Granted for isolating a compromised server.
- **Negative Shaping**: Penalties are applied for blocking legitimate IPs (-0.5) or isolating healthy infrastructure (-0.7).

## Setup & Usage

### Local Development
```bash
pip install -r requirements.txt
python server.py
```

### Running Inference
```bash
export HF_TOKEN="your_token"
export MODEL_NAME="gpt-4o"
python inference.py
```

### Docker
```bash
docker build -t siem-security-env .
docker run -p 7860:7860 -e HF_TOKEN="your_token" siem-security-env
```

## Baseline Results
The environment has been validated with GPT-4o, showing a clear learning curve across the three tasks, with typical scores ranging from 0.8 to 1.0.
