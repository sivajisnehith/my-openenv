from fastapi import FastAPI, HTTPException
from models import Observation, Action, Reward
from environment import SIEMEnvironment
from tasks import TASKS
from graders import calculate_score
from typing import Dict, Any

app = FastAPI(title="SIEM Security OpenEnv")

# In-memory store for environments (by scenario/task)
envs: Dict[str, SIEMEnvironment] = {}

@app.get("/")
async def root():
    return {"message": "SIEM Security OpenEnv is running", "tasks": [t.id for t in TASKS]}

@app.post("/reset")
@app.get("/reset")
async def reset(task_id: str = "task_1") -> Observation:
    task = next((t for t in TASKS if t.id == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    env = SIEMEnvironment(scenario_id=task.scenario_id)
    envs[task_id] = env
    return env.reset()

@app.get("/state")
async def state(task_id: str = "task_1") -> Observation:
    if task_id not in envs:
        raise HTTPException(status_code=404, detail="Environment not initialized for this task. Call /reset first.")
    return envs[task_id].state()

@app.post("/step")
async def step(action: Action, task_id: str = "task_1") -> Dict[str, Any]:
    if task_id not in envs:
        raise HTTPException(status_code=404, detail="Environment not initialized. Call /reset first.")
    
    env = envs[task_id]
    obs, reward, done, info = env.step(action)
    
    score = 0.0
    if done:
        score = calculate_score(task_id, env)
    
    return {
        "observation": obs.model_dump(),
        "reward": reward,
        "done": done,
        "info": info,
        "score": score
    }

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
