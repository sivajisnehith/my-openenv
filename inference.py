import os
import json
import asyncio
import textwrap
from typing import List, Optional
from openai import OpenAI

# Environment-specific imports
from environment import SIEMEnvironment
from models import Action, ActionType
from tasks import TASKS
from graders import calculate_score

# Environment variables for configuration (as per Mandatory Instructions)
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
API_KEY = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")

# Initialize OpenAI Client
client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

async def get_agent_action(obs, task_description) -> (Action, Optional[str]):
    prompt = textwrap.dedent(f"""
        You are a SOC Analyst investigating a security alert.
        Task: {task_description}
        
        Current System State:
        System Status: {json.dumps(obs.system_status)}
        Recent Logs: {json.dumps([l.model_dump() for l in obs.logs[-10:]])}
        Active Alerts: {obs.active_alerts}
        
        Choose exactly one action from:
        - query_logs (no params)
        - block_ip (params: {{"ip": "X.X.X.X"}})
        - isolate_server (params: {{"server": "name"}})
        - mark_safe (no params)
        
        Return ONLY a JSON object: {{"action_type": "...", "parameters": {{...}}}}
    """).strip()
    
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return Action(**data), None
    except Exception as e:
        return Action(action_type=ActionType.QUERY_LOGS, parameters={}), str(e)

async def run_task(task):
    env = SIEMEnvironment(scenario_id=task.scenario_id)
    benchmark_name = "siem-security-openenv"
    
    log_start(task=task.id, env=benchmark_name, model=MODEL_NAME)
    
    steps_taken = 0
    rewards = []
    success = False
    score = 0.0
    
    try:
        obs = env.reset()
        done = False
        
        for step in range(1, 11): # Max 10 steps
            if done: break
            
            action, error = await get_agent_action(obs, task.description)
            action_str = f"{action.action_type}({json.dumps(action.parameters)})"
            
            obs, reward, done, info = env.step(action)
            rewards.append(reward)
            steps_taken = step
            
            log_step(step=step, action=action_str, reward=reward, done=done, error=error)
            
        score = calculate_score(task.id, env)
        success = score >= 1.0
        
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

async def main():
    if not API_KEY:
        print("ERROR: HF_TOKEN or OPENAI_API_KEY environment variable is required.")
        return

    for task in TASKS:
        await run_task(task)

if __name__ == "__main__":
    asyncio.run(main())
