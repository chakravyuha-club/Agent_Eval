from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
from app.db.session import get_db
from app.models.models import Competition, Dataset, Announcement
from app.schemas.schemas import CompetitionResponse, DatasetResponse, AnnouncementResponse

router = APIRouter(prefix="/competition", tags=["Competition"])

@router.get("", response_model=CompetitionResponse)
def get_competition_details(db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=404, detail="No active competition found.")
    return comp

@router.get("/problem")
def get_problem_statement(db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    return {
        "title": comp.name if comp else "18-Hour AI Agent Building Competition",
        "description": comp.description if comp else "",
        "objective": "Design, build, and deploy an autonomous AI Agent that executes multi-step domain tasks, satisfies assertions, and maintains high reliability, tool accuracy, safety, and efficiency.",
        "evaluation_dimensions": [
            {"dimension": "Dimension A", "name": "Task Performance", "metrics": "Task Success Rate (TSR), Outcome Correctness, Assertion Satisfaction, F1 Score"},
            {"dimension": "Dimension B", "name": "Agentic Behavior", "metrics": "Tool Selection Accuracy, Argument Validity, Trajectory Efficiency, Error Recovery"},
            {"dimension": "Dimension C", "name": "Reliability", "metrics": "pass@1, pass^3 (All 3 Consecutive Runs), Timeout & Failure Rate"},
            {"dimension": "Dimension D", "name": "Output Quality", "metrics": "Schema Compliance, Groundedness, Negative Instruction Following"},
            {"dimension": "Dimension E", "name": "Safety & Constraints", "metrics": "Adversarial Injection Resistance, SSRF Sandboxing, Secret Leak Prevention"},
            {"dimension": "Dimension F", "name": "Operational Efficiency", "metrics": "P50 / P95 Latency Profiles, Token Overhead"}
        ],
        "stages": [
            {"stage": 1, "name": "Stage 1: Prediction-File Evaluation", "format": "CSV/XLSX Tabular Submission", "qualification": "Top 20 Teams Advance"},
            {"stage": 2, "name": "Stage 2: Live Deployed Agent Testing", "format": "HTTP API (/health & /predict)", "outcome": "Top 3 Winners Crowned"}
        ],
        "rules": [
            "All submissions must be authored by registered team members.",
            "Stage 1 allows CSV/XLSX predictions conforming to schema.",
            "Stage 2 endpoints must respond to /health and /predict with latency under 10 seconds.",
            "Adversarial or abusive requests against platform infrastructure will lead to disqualification."
        ]
    }

@router.get("/datasets", response_model=List[DatasetResponse])
def get_public_datasets(db: Session = Depends(get_db)):
    # Explicitly return only public datasets (training, public_test, schema). Private datasets are NEVER exposed.
    datasets = db.query(Dataset).filter(Dataset.dataset_type.in_(["training", "public_test", "schema"])).all()
    return datasets

@router.get("/datasets/{dataset_id}/download")
def download_dataset(dataset_id: str, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset or dataset.dataset_type == "private_test":
        raise HTTPException(status_code=404, detail="Dataset not found or access restricted.")
    
    # Map to local dataset file
    filename = os.path.basename(dataset.storage_path)
    file_path = os.path.join(os.getcwd(), "datasets", filename)
    if not os.path.exists(file_path):
        file_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Dataset file not found on storage server.")
    
    return FileResponse(file_path, filename=filename, media_type="text/csv")

@router.get("/announcements", response_model=List[AnnouncementResponse])
def get_announcements(db: Session = Depends(get_db)):
    announcements = db.query(Announcement).order_by(Announcement.published_at.desc()).all()
    return announcements
