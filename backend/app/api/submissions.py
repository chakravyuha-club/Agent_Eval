import os
import uuid
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi.concurrency import run_in_threadpool
from app.core.config import settings
from app.db.session import get_db
from app.models.models import User, Team, Submission, EvaluationJob, EvaluationResult, Competition, TaskResult
from app.schemas.schemas import SubmissionResponse, EvaluationResultResponse, Stage2SubmissionCreate
from app.api.deps import get_current_user, get_current_team_leader
from app.services.evaluation_service import process_evaluation_job
from evaluator.stage1.evaluator import validate_prediction_file
from evaluator.safety.ssrf_validator import validate_and_resolve

router = APIRouter(prefix="/submissions", tags=["Submissions"])

def utcnow():
    return datetime.now(timezone.utc)

def as_aware(dt):
    """SQLite/Postgres `DateTime` columns return NAIVE datetimes; comparing them with an aware `now` raises TypeError."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)

def require_submitting_team(team):
    if team is None:
        raise HTTPException(status_code=403, detail="Administrator accounts cannot submit on behalf of a team.")
    return team

def assert_stage_open(comp, stage: int):
    """Server-side deadline / state enforcement (the old check was inverted and crashed on naive datetimes)."""
    if comp.status == "completed":
        raise HTTPException(status_code=403, detail="The competition has ended.")
    if stage == 1:
        if comp.status != "active" or comp.current_stage != 1:
            raise HTTPException(status_code=403, detail="Stage 1 submissions are closed.")
        deadline = as_aware(comp.stage_1_deadline)
    else:
        if comp.status != "stage2_open":
            raise HTTPException(status_code=403, detail="Stage 2 is not open.")
        deadline = as_aware(comp.stage_2_deadline)
    if deadline and utcnow() > deadline:
        raise HTTPException(status_code=403, detail=f"Stage {stage} submission deadline has passed.")

async def run_job(job_id, db):
    """Inline scoring only in dev; in production the worker process picks the queued job up."""
    if settings.EVALUATE_INLINE:
        await run_in_threadpool(process_evaluation_job, job_id, db)

def _failure_counts(task_items):
    out = {}
    for tr in task_items:
        if not tr.passed:
            k = tr.safe_error_category or "failed"
            out[k] = out.get(k, 0) + 1
    return out

@router.post("/stage-1", response_model=SubmissionResponse)
async def submit_stage_1_file(
    file: UploadFile = File(...),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    require_submitting_team(team)
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    assert_stage_open(comp, 1)

    cap = settings.MAX_SUBMISSIONS_PER_TEAM_STAGE1
    if cap and db.query(Submission).filter(Submission.team_id == team.id, Submission.stage == 1).count() >= cap:
        raise HTTPException(status_code=429, detail=f"Submission limit reached ({cap} per team).")

    # Bounded read: never buffer more than limit+1 bytes
    limit = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    file_bytes = await file.read(limit + 1)
    if len(file_bytes) > limit:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB maximum size limit.")

    is_valid, err_msg, df = validate_prediction_file(file_bytes, file.filename or "", max_rows=settings.STAGE1_MAX_ROWS)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"File validation failed: {err_msg}")

    # Save file to storage
    storage_dir = os.path.join(settings.STORAGE_BASE_DIR, "uploads")
    os.makedirs(storage_dir, exist_ok=True)
    
    sub_count = db.query(Submission).filter(Submission.team_id == team.id, Submission.stage == 1).count()
    version = sub_count + 1
    
    ext = os.path.splitext(file.filename or "")[1].lower()
    saved_filename = f"{team.team_code}_stage1_v{version}_{uuid.uuid4().hex[:8]}{ext}"  # unique: no overwrite on races
    saved_path = os.path.join(storage_dir, saved_filename)
    
    with open(saved_path, "wb") as f:
        f.write(file_bytes)

    sub = Submission(
        team_id=team.id,
        stage=1,
        submission_version=version,
        file_storage_path=saved_path,
        status="queued",
        is_official=True
    )
    db.add(sub)
    db.flush()

    job = EvaluationJob(
        submission_id=sub.id,
        team_id=team.id,
        stage=1,
        status="queued",
        max_attempts=settings.JOB_MAX_ATTEMPTS
    )
    db.add(job)
    db.commit()

    await run_job(job.id, db)
    db.refresh(sub)

    return SubmissionResponse(
        id=sub.id,
        team_id=sub.team_id,
        team_name=team.team_name,
        stage=sub.stage,
        submission_type="file_upload",
        submission_version=sub.submission_version,
        status=sub.status,
        submitted_at=sub.submitted_at,
        selected_for_evaluation=True
    )

@router.post("/stage-2", response_model=SubmissionResponse)
async def submit_stage_2_url(
    payload: Stage2SubmissionCreate,
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    require_submitting_team(team)
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    assert_stage_open(comp, 2)

    if team.qualification_status != "qualified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Stage 1 qualified teams are permitted to submit in Stage 2."
        )
    cap = settings.MAX_SUBMISSIONS_PER_TEAM_STAGE2
    if cap and db.query(Submission).filter(Submission.team_id == team.id, Submission.stage == 2).count() >= cap:
        raise HTTPException(status_code=429, detail=f"Submission limit reached ({cap} per team).")
    # Fail fast with an actionable message instead of creating a doomed job
    ok, err, _ = validate_and_resolve(
        payload.application_url.strip(), require_https=settings.STAGE2_REQUIRE_HTTPS,
        allow_localhost_for_testing=settings.STAGE2_ALLOW_LOCALHOST_DEV)
    if not ok:
        raise HTTPException(status_code=400, detail=f"Invalid agent endpoint: {err}")

    sub_count = db.query(Submission).filter(Submission.team_id == team.id, Submission.stage == 2).count()
    version = sub_count + 1

    sub = Submission(
        team_id=team.id,
        stage=2,
        submission_version=version,
        application_url=payload.application_url.strip(),
        status="queued",
        is_official=True
    )
    db.add(sub)
    db.flush()

    job = EvaluationJob(
        submission_id=sub.id,
        team_id=team.id,
        stage=2,
        status="queued",
        max_attempts=settings.JOB_MAX_ATTEMPTS
    )
    db.add(job)
    db.commit()

    await run_job(job.id, db)
    db.refresh(sub)

    return SubmissionResponse(
        id=sub.id,
        team_id=sub.team_id,
        team_name=team.team_name,
        stage=sub.stage,
        submission_type="deployed_url",
        application_url=sub.application_url,
        submission_version=sub.submission_version,
        status=sub.status,
        submitted_at=sub.submitted_at,
        selected_for_evaluation=True
    )

@router.get("/my", response_model=List[SubmissionResponse])
def get_my_submissions(
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    if team is None:  # admin accounts have no team
        return []
    subs = db.query(Submission).filter(Submission.team_id == team.id).order_by(Submission.submitted_at.desc()).all()
    return [
        SubmissionResponse(
            id=s.id,
            team_id=s.team_id,
            team_name=team.team_name,
            stage=s.stage,
            submission_type="file_upload" if s.stage == 1 else "deployed_url",
            application_url=s.application_url,
            submission_version=s.submission_version,
            status=s.status,
            submitted_at=s.submitted_at,
            selected_for_evaluation=True
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

    is_admin = current_user.role == "admin"
    # 404 (not 403) for other teams' submissions so ids cannot be probed
    if not is_admin and (team is None or sub.team_id != team.id):
        raise HTTPException(status_code=404, detail="Submission not found.")
    owner = db.query(Team).filter(Team.id == sub.team_id).first()

    eval_res = db.query(EvaluationResult).filter(EvaluationResult.submission_id == sub.id).first()
    if not eval_res:
        raise HTTPException(status_code=404, detail="Evaluation results not available yet for this submission.")

    task_items = db.query(TaskResult).filter(TaskResult.evaluation_result_id == eval_res.id).all()

    return {
        "id": eval_res.id,
        "submission_id": sub.id,
        "team_id": sub.team_id,
        "team_name": owner.team_name if owner else None,
        "stage": eval_res.stage,
        "evaluator_version": eval_res.evaluator_version,
        "rubric_version": eval_res.rubric_version,
        "total_score": eval_res.total_score,
        "task_success_rate": eval_res.task_success_rate,
        "metrics": eval_res.metrics_json,
        "score_breakdown": eval_res.score_breakdown_json,
        "result_status": eval_res.result_status,
        "created_at": eval_res.created_at,
        # Per-task pass/fail on HIDDEN tasks is a label oracle -> admins only. Teams get category counts.
        "task_results": [
            {"task_id": tr.task_id, "passed": tr.passed, "latency_ms": tr.latency_ms,
             "safe_error_category": tr.safe_error_category} for tr in task_items
        ] if is_admin else [],
        "failure_summary": {} if is_admin else _failure_counts(task_items),
    }

@router.get("/{submission_id}/report")
def get_submission_report(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    team: Team = Depends(get_current_team_leader),
    db: Session = Depends(get_db)
):
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found.")

    if current_user.role != "admin" and (team is None or sub.team_id != team.id):
        raise HTTPException(status_code=404, detail="Submission not found.")
    team = db.query(Team).filter(Team.id == sub.team_id).first()

    eval_res = db.query(EvaluationResult).filter(EvaluationResult.submission_id == sub.id).first()
    if not eval_res:
        raise HTTPException(status_code=404, detail="Evaluation results not available.")

    return {
        "submission_id": sub.id,
        "team_name": team.team_name if team else "Unknown",
        "stage": sub.stage,
        "submission_version": sub.submission_version,
        "submitted_at": sub.submitted_at,
        "status": sub.status,
        "total_score": eval_res.total_score,
        "task_success_rate": eval_res.task_success_rate,
        "metrics": eval_res.metrics_json,
        "score_breakdown": eval_res.score_breakdown_json
    }
