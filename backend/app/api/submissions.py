import os
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.session import get_db
from app.models.models import User, Team, Submission, EvaluationJob, EvaluationResult, Competition, TaskResult
from app.schemas.schemas import SubmissionResponse, EvaluationResultResponse, Stage2SubmissionCreate
from app.api.deps import get_current_user, get_current_team_leader
from app.services.evaluation_service import process_evaluation_job
from evaluator.stage1.evaluator import validate_prediction_file

router = APIRouter(prefix="/submissions", tags=["Submissions"])

def utcnow():
    return datetime.now(timezone.utc)

@router.post("/stage-1", response_model=SubmissionResponse)
async def submit_stage_1_file(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    
    # Check deadline
    if comp.stage_1_deadline and utcnow() > comp.stage_1_deadline and comp.status != "active":
        raise HTTPException(status_code=400, detail="Stage 1 submission deadline has passed.")

    # Read and validate file in-memory
    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 50MB maximum size limit.")

    is_valid, err_msg, df = validate_prediction_file(file_bytes, file.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"File validation failed: {err_msg}")

    # Save file to storage
    storage_dir = os.path.join(os.getcwd(), "storage", "uploads")
    os.makedirs(storage_dir, exist_ok=True)
    
    sub_count = db.query(Submission).filter(Submission.team_id == team.id, Submission.stage == 1).count()
    version = sub_count + 1
    
    ext = os.path.splitext(file.filename)[1]
    saved_filename = f"{team.team_code}_stage1_v{version}{ext}"
    saved_path = os.path.join(storage_dir, saved_filename)
    
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    # Create Submission record
    sub = Submission(
        team_id=team.id,
        competition_id=comp.id,
        stage=1,
        submission_type="file",
        file_storage_path=saved_path,
        notes=notes,
        submission_version=version,
        status="submitted",
        selected_for_evaluation=True
    )
    db.add(sub)
    db.flush()

    # Create Evaluation Job
    job = EvaluationJob(
        submission_id=sub.id,
        team_id=team.id,
        stage=1,
        status="queued",
        attempt_count=1
    )
    db.add(job)
    db.commit()

    # Process evaluation immediately in background/synchronously for smooth demo
    process_evaluation_job(job.id, db)

    return SubmissionResponse(
        id=sub.id,
        team_id=team.id,
        team_name=team.team_name,
        stage=1,
        submission_type="file",
        submission_version=version,
        status=sub.status,
        submitted_at=sub.submitted_at,
        selected_for_evaluation=sub.selected_for_evaluation
    )

@router.post("/stage-2", response_model=SubmissionResponse)
def submit_stage_2_url(
    payload: Stage2SubmissionCreate,
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")

    # Verify qualification
    if team.qualification_status != "qualified" and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Stage 1 qualified teams are permitted to submit in Stage 2."
        )

    sub_count = db.query(Submission).filter(Submission.team_id == team.id, Submission.stage == 2).count()
    version = sub_count + 1

    sub = Submission(
        team_id=team.id,
        competition_id=comp.id,
        stage=2,
        submission_type="url",
        application_url=payload.application_url.strip(),
        notes=payload.notes,
        submission_version=version,
        status="submitted",
        selected_for_evaluation=True
    )
    db.add(sub)
    db.flush()

    job = EvaluationJob(
        submission_id=sub.id,
        team_id=team.id,
        stage=2,
        status="queued",
        attempt_count=1
    )
    db.add(job)
    db.commit()

    # Process evaluation
    process_evaluation_job(job.id, db)

    return SubmissionResponse(
        id=sub.id,
        team_id=team.id,
        team_name=team.team_name,
        stage=2,
        submission_type="url",
        application_url=sub.application_url,
        submission_version=version,
        status=sub.status,
        submitted_at=sub.submitted_at,
        selected_for_evaluation=sub.selected_for_evaluation
    )

@router.get("/my", response_model=List[SubmissionResponse])
def get_my_submissions(
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    subs = db.query(Submission).filter(Submission.team_id == team.id).order_by(Submission.submitted_at.desc()).all()
    return [
        SubmissionResponse(
            id=s.id,
            team_id=s.team_id,
            team_name=team.team_name,
            stage=s.stage,
            submission_type=s.submission_type,
            application_url=s.application_url,
            submission_version=s.submission_version,
            status=s.status,
            submitted_at=s.submitted_at,
            selected_for_evaluation=s.selected_for_evaluation
        ) for s in subs
    ]

@router.get("/{submission_id}/results")
def get_submission_results(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Ensure team can only view their own results (unless admin)
    if sub.team_id != team.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied to another team's private evaluation results.")

    eval_res = db.query(EvaluationResult).filter(EvaluationResult.submission_id == sub.id).first()
    if not eval_res:
        return {"status": "pending", "message": "Evaluation in progress or not yet evaluated."}

    # Fetch task results (safe high level summary, NEVER exposing hidden labels or prompts)
    task_items = db.query(TaskResult).filter(TaskResult.evaluation_result_id == eval_res.id).all()
    
    return {
        "id": eval_res.id,
        "submission_id": sub.id,
        "team_id": sub.team_id,
        "team_name": team.team_name,
        "stage": eval_res.stage,
        "evaluator_version": eval_res.evaluator_version,
        "rubric_version": eval_res.rubric_version,
        "total_score": eval_res.total_score,
        "task_success_rate": eval_res.task_success_rate,
        "metrics": eval_res.metrics_json,
        "score_breakdown": eval_res.score_breakdown_json,
        "result_status": eval_res.result_status,
        "created_at": eval_res.created_at,
        "task_results": [
            {
                "task_id": tr.task_id,
                "passed": tr.passed,
                "latency_ms": tr.latency_ms,
                "safe_error_category": tr.safe_error_category
            } for tr in task_items
        ]
    }

@router.get("/{submission_id}/report")
def download_team_report(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    if sub.team_id != team.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied.")

    eval_res = db.query(EvaluationResult).filter(EvaluationResult.submission_id == sub.id).first()
    if not eval_res:
        raise HTTPException(status_code=404, detail="No evaluation results available for this submission.")

    report_content = {
        "report_title": f"AgentScore Evaluation Report — {team.team_name}",
        "team_code": team.team_code,
        "stage": f"Stage {eval_res.stage}",
        "evaluation_timestamp": eval_res.created_at.isoformat(),
        "evaluator_version": eval_res.evaluator_version,
        "overall_score": eval_res.total_score,
        "task_success_rate_percent": eval_res.task_success_rate,
        "multi_dimensional_metrics": eval_res.metrics_json,
        "score_breakdown": eval_res.score_breakdown_json,
        "qualification_status": team.qualification_status
    }

    return JSONResponse(
        content=report_content,
        headers={"Content-Disposition": f"attachment; filename=AgentScore_{team.team_code}_Report.json"}
    )
