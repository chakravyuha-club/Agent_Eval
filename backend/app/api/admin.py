import csv
import io
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import (
    User, Team, TeamMember, Competition, Submission, EvaluationJob, 
    EvaluationResult, RubricVersion, LeaderboardSnapshot, AuditLog
)
from app.schemas.schemas import (
    AdminDashboardStats, TeamResponse, TeamCreateRequest, 
    TeamUpdateRequest, RubricSchema, AuditLogResponse, EvaluationJobResponse
)
from app.api.deps import require_admin
from app.core.config import settings
from app.services.preflight import run_preflight
from app.core.security import get_password_hash
from app.services.team_service import bulk_import_teams_from_csv, reset_team_leader_password
from app.services.evaluation_service import (
    process_evaluation_job,
    freeze_stage1_and_qualify_top20,
    freeze_final_and_select_top3,
    StateError
)

router = APIRouter(prefix="/admin", tags=["Administrator"])

@router.get("/dashboard/stats", response_model=AdminDashboardStats)
def get_admin_dashboard_stats(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    total_teams = db.query(Team).count()
    teams_stage1 = db.query(Submission.team_id).filter(Submission.stage == 1).distinct().count()
    teams_stage2 = db.query(Submission.team_id).filter(Submission.stage == 2).distinct().count()
    
    pending_evals = db.query(EvaluationJob).filter(EvaluationJob.status.in_(["queued", "evaluating"])).count()
    completed_evals = db.query(EvaluationJob).filter(EvaluationJob.status == "completed").count()
    failed_evals = db.query(EvaluationJob).filter(EvaluationJob.status == "failed").count()
    qualified_teams = db.query(Team).filter(Team.qualification_status == "qualified").count()

    comp = db.query(Competition).first()

    return AdminDashboardStats(
        total_teams=total_teams,
        teams_submitted_stage1=teams_stage1,
        teams_submitted_stage2=teams_stage2,
        pending_evaluations=pending_evals,
        completed_evaluations=completed_evals,
        failed_evaluations=failed_evals,
        qualified_teams_count=qualified_teams,
        competition_stage=comp.current_stage if comp else 1,
        competition_status=comp.status if comp else "active"
    )

@router.get("/teams", response_model=List[TeamResponse])
def list_all_teams(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.created_at.asc()).all()
    return teams

@router.post("/teams", response_model=TeamResponse)
def create_team(req: TeamCreateRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    existing = db.query(Team).filter(Team.team_code == req.team_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Team code '{req.team_code}' already exists.")

    existing_user = db.query(User).filter(User.email == req.leader_email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail=f"Email '{req.leader_email}' is already registered.")

    # Create User for Leader
    leader_user = User(
        email=req.leader_email,
        hashed_password=get_password_hash(req.leader_password),
        role="team_leader",
        is_active=True
    )
    db.add(leader_user)
    db.flush()

    # Create Team
    team = Team(
        team_code=req.team_code,
        team_name=req.team_name,
        leader_user_id=leader_user.id,
        qualification_status="registered"
    )
    db.add(team)
    db.flush()

    # Add Members
    for member in req.members:
        db.add(TeamMember(
            team_id=team.id,
            name=member.name,
            email=member.email,
            is_leader=member.is_leader
        ))

    db.add(AuditLog(
        actor_user_id=admin.id,
        action="CREATE_TEAM",
        entity_type="Team",
        entity_id=team.id,
        details_json={"team_code": team.team_code, "team_name": team.team_name}
    ))
    db.commit()
    db.refresh(team)
    return team

@router.post("/teams/import")
async def import_teams_csv(
    file: UploadFile = File(...),
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    content = await file.read()
    try:
        csv_text = content.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content.decode("latin-1")

    generated: list = []
    imported, errors = bulk_import_teams_from_csv(csv_text, db, admin.id, credentials_out=generated)
    return {
        "status": "success",
        # Passwords generated for rows that had none. Shown ONCE - hand them out securely; never stored in clear.
        "generated_credentials": generated,
        "imported_count": imported,
        "error_count": len(errors),
        "errors": errors[:10] # Return first 10 errors if any
    }

@router.post("/teams/{team_id}/reset-password")
def reset_password(
    team_id: str,
    new_password: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if new_password is not None and len(new_password) < 12:
        raise HTTPException(status_code=422, detail="Password must be at least 12 characters.")
    pwd = new_password or secrets.token_urlsafe(12) + "aA1"   # never a shared default
    success = reset_team_leader_password(team_id, pwd, db, admin.id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found.")
    # Returned once, over TLS, to the admin.
    return {"status": "success", "new_password": pwd}

@router.get("/evaluations")
def list_evaluations(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    jobs = db.query(EvaluationJob).order_by(EvaluationJob.queued_at.desc()).limit(100).all()
    results = []
    for job in jobs:
        results.append({
            "id": job.id,
            "submission_id": job.submission_id,
            "team_id": job.team_id,
            "stage": job.stage,
            "status": job.status,
            "attempt_count": job.attempt_count,
            "queued_at": job.queued_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "error_summary": job.error_summary,
            "total_score": job.result.total_score if job.result else None
        })
    return results

@router.post("/evaluations/{job_id}/retry")
def retry_evaluation(job_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Evaluation job not found.")
    
    job.status = "queued"
    job.attempt_count += 1
    job.error_summary = None
    db.commit()

    db.add(AuditLog(
        actor_user_id=admin.id,
        action="RETRY_EVALUATION",
        entity_type="EvaluationJob",
        entity_id=job.id,
        details_json={"submission_id": job.submission_id, "attempt": job.attempt_count}
    ))
    db.commit()

    if settings.EVALUATE_INLINE:
        process_evaluation_job(job.id, db)
    return {"status": "success", "message": f"Job {job.id} queued for retry."}

@router.post("/evaluations/start-all-pending")
def start_all_pending(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    queued_jobs = db.query(EvaluationJob).filter(EvaluationJob.status == "queued").all()
    count = len(queued_jobs)
    if settings.EVALUATE_INLINE:
        for job in queued_jobs:
            process_evaluation_job(job.id, db)
    db.add(AuditLog(
        actor_user_id=admin.id,
        action="START_ALL_PENDING_EVALUATIONS",
        entity_type="EvaluationJob",
        details_json={"count": count}
    ))
    db.commit()
    return {"status": "success", "processed_jobs_count": count}

@router.post("/stage-1/freeze-and-qualify")
def freeze_stage_1(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    try:
        return freeze_stage1_and_qualify_top20(comp.id, db, admin.id)
    except StateError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))

@router.post("/stage-2/open")
def open_stage_2(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    if comp.status != "frozen_stage1":
        raise HTTPException(status_code=409, detail="Stage 2 can only be opened after Stage 1 has been frozen.")
    comp.current_stage = 2
    comp.status = "stage2_open"
    db.add(AuditLog(actor_user_id=admin.id, action="OPEN_STAGE2", entity_type="Competition", entity_id=comp.id, details_json={}))
    db.commit()
    return {"status": "success", "message": "Stage 2 is now open for qualified teams."}

@router.post("/final-results/freeze")
def freeze_final_results(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    try:
        return freeze_final_and_select_top3(comp.id, db, admin.id)
    except StateError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/rubrics")
def list_rubrics(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rubrics = db.query(RubricVersion).order_by(RubricVersion.created_at.desc()).all()
    return rubrics

@router.post("/rubrics")
def create_or_update_rubric(rubric_data: RubricSchema, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if comp and comp.status in ["frozen_stage1", "stage2_open", "frozen_final", "completed"]:
        raise HTTPException(status_code=409, detail="Rubrics cannot be modified after Stage 1 has been frozen.")

    new_rubric = RubricVersion(
        stage=rubric_data.stage,
        version=rubric_data.version,
        rubric_json=rubric_data.model_dump(),
        is_locked=True,
        created_by_user_id=admin.id
    )
    db.add(new_rubric)
    db.add(AuditLog(
        actor_user_id=admin.id,
        action="UPDATE_RUBRIC",
        entity_type="RubricVersion",
        details_json=rubric_data.model_dump()
    ))
    db.commit()
    db.refresh(new_rubric)
    return new_rubric

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    output = []
    for l in logs:
        output.append(AuditLogResponse(
            id=l.id,
            actor_email=l.actor.email if l.actor else "System",
            action=l.action,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            details=l.details_json,
            created_at=l.created_at
        ))
    return output

@router.get("/export/results.csv")
def export_results_csv(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.final_score.desc(), Team.stage2_score.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Final Rank", "Team Code", "Team Name", "Stage 1 Score", 
        "Stage 2 Score", "Final Score (Composite)", "Qualification Status"
    ])

    for idx, t in enumerate(teams, start=1):
        writer.writerow([
            t.rank_final or idx,
            t.team_code,
            t.team_name,
            t.stage1_score,
            t.stage2_score,
            t.final_score,
            t.qualification_status
        ])

    output.seek(0)
    db.add(AuditLog(actor_user_id=admin.id, action="EXPORT_RESULTS_CSV", entity_type="Team", details_json={}))
    db.commit()
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=AgentScore_Official_Results.csv"}
    )

@router.get("/preflight")
def preflight(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Go/no-go report. `ready` is False while any blocking check fails."""
    checks = run_preflight(settings, db)
    return {"ready": all(c["ok"] for c in checks if c["blocking"]), "checks": checks}
