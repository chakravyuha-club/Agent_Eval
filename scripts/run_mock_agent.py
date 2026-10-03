"""
Mock Deployed AI Agent Server for Stage 2 Testing
Runs an HTTP server conforming to the AgentScore Stage 2 API Contract.
"""
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import time

app = FastAPI(title="Mock Agent - Team01", version="1.0.0")

class PredictRequest(BaseModel):
    task_id: str
    stage: Optional[str] = "stage_2"
    input: Dict[str, Any]
    constraints: Optional[Dict[str, Any]] = None

class TrajectoryStep(BaseModel):
    step: int
    tool: str
    args: Dict[str, Any]
    output: str

class PredictResponse(BaseModel):
    task_id: str
    status: str
    prediction: Dict[str, Any]
    explanation: Optional[str] = None
    trajectory: Optional[List[TrajectoryStep]] = None

@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "agent_name": "Team01-ProductionAgent"
    }

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    time.sleep(0.05) # Simulated 50ms realistic latency
    query = req.input.get("query", "").lower()
    
    # Check for adversarial prompt injection
    if "ignore all previous instructions" in query or "secret key" in query or "rm -rf" in query:
        return PredictResponse(
            task_id=req.task_id,
            status="success",
            prediction={"action": "safe_refusal", "reason": "Security constraint violation detected."},
            explanation="Safety guardrail triggered to prevent prompt injection or dangerous command.",
            trajectory=[
                TrajectoryStep(step=1, tool="safety_classifier", args={"query": query}, output="Adversarial attack detected.")
            ]
        )
    
    # Realistic task predictions
    return PredictResponse(
        task_id=req.task_id,
        status="success",
        prediction={
            "label": "optimal_solution",
            "decision": "approved",
            "computed_value": 4850.0
        },
        explanation="Task executed successfully with validated constraints.",
        trajectory=[
            TrajectoryStep(step=1, tool="data_retrieval", args={"query": query}, output="Fetched 5 context records"),
            TrajectoryStep(step=2, tool="constraint_verifier", args={"budget": 10000}, output="Passed all rules")
        ]
    )

if __name__ == "__main__":
    print("Starting Mock AI Agent on http://localhost:8080...")
    uvicorn.run(app, host="127.0.0.1", port=8080)
