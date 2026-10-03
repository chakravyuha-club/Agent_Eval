import csv
import io
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import (
    User, Team, TeamMember, Competition, Dataset, Submission,
    EvaluationJob, EvaluationResult, RubricVersion, AuditLog
)
from app.schemas.schemas import (
    AdminDashboardStats, TeamResponse, TeamMemberResponse, TeamCreateRequest,
    TeamUpdateRequest, RubricSchema, AuditLogResponse, EvaluationJobResponse
)
from app.api.deps import require_admin
from app.core.security import get_password_hash
from app.services.team_service import bulk_import_teams_from_csv, reset_team_leader_password
from app.services.evaluation_service import (
    process_evaluation_job,
    freeze_stage1_and_qualify_top20,
    freeze_final_and_select_top3
)

router = APIRouter(prefix="/admin", tags=["Administrator"])

def utcnow():
    return datetime.now(timezone.utc)

@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    comp = db.query(Competition).first()
    total_teams = db.query(Team).count()
    sub_stage1 = db.query(Submission.team_id).filter(Submission.stage == 1).distinct().count()
    sub_stage2 = db.query(Submission.team_id).filter(Submission.stage == 2).distinct().count()
    
    pending_jobs = db.query(EvaluationJob).filter(EvaluationJob.status.in_(["queued", "evaluating"])).count()
    completed_jobs = db.query(EvaluationJob).filter(EvaluationJob.status == "passed").count()
    failed_jobs = db.query(EvaluationJob).filter(EvaluationJob.status == "failed").count()
    
    qualified_teams = db.query(Team).filter(Team.qualification_status == "qualified").count()

    return AdminDashboardStats(
        total_teams=total_teams,
        teams_submitted_stage1=sub_stage1,
        teams_submitted_stage2=sub_stage2,
        pending_evaluations=pending_jobs,
        completed_evaluations=completed_jobs,
        failed_evaluations=failed_jobs,
        qualified_teams_count=qualified_teams,
        competition_stage=comp.current_stage if comp else 1,
        competition_status=comp.status if comp else "active"
    )

@router.get("/teams", response_model=List[TeamResponse])
def list_teams(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    teams = db.query(Team).order_by(Team.team_code.asc()).all()
    results = []
    for t in teams:
        members = [
            TeamMemberResponse(id=m.id, name=m.name, email=m.email, is_leader=m.is_leader)
            for m in t.members
        ]
        results.append(TeamResponse(
            id=t.id,
            team_code=t.team_code,
            team_name=t.team_name,
            qualification_status=t.qualification_status,
            stage1_score=t.stage1_score,
            stage2_score=t.stage2_score,
            final_score=t.final_score,
            stage1_rank=t.stage1_rank,
            final_rank=t.final_rank,
            members=members,
            created_at=t.created_at
        ))
    return results

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

    imported, errors = bulk_import_teams_from_csv(csv_text, db, admin.id)
    return {
        "status": "success",
        "imported_count": imported,
        "error_count": len(errors),
        "errors": errors[:10] # Return first 10 errors if any
    }

@router.post("/teams/{team_id}/reset-credentials")
def reset_credentials(
    team_id: str,
    new_password: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    pwd = new_password or "ResetPass2026!"
    success = reset_team_leader_password(team_id, pwd, db, admin.id)
    if not success:
        raise HTTPException(status_code=404, detail="Team not found.")
    return {"status": "success", "message": f"Password reset to '{pwd}'."}

@router.get("/evaluations")
def list_evaluations(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    jobs = db.query(EvaluationJob).order_by(EvaluationJob.queued_at.desc()).limit(100).all()
    out = []
    for j in jobs:
        t = db.query(Team).filter(Team.id == j.team_id).first()
        out.append({
            "id": j.id,
            "submission_id": j.submission_id,
            "team_id": j.team_id,
            "team_code": t.team_code if t else "unknown",
            "team_name": t.team_name if t else "unknown",
            "stage": j.stage,
            "status": j.status,
            "attempt_count": j.attempt_count,
            "queued_at": j.queued_at,
            "started_at": j.started_at,
            "completed_at": j.completed_at,
            "error_summary": j.error_summary
        })
    return out

@router.post("/evaluations/start")
def start_pending_evaluations(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    jobs = db.query(EvaluationJob).filter(EvaluationJob.status == "queued").all()
    processed = 0
    for j in jobs:
        process_evaluation_job(j.id, db)
        processed += 1
    return {"status": "success", "processed_jobs": processed}

@router.post("/evaluations/{job_id}/retry")
def retry_evaluation(job_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    
    job.status = "queued"
    job.attempt_count += 1
    db.commit()

    process_evaluation_job(job.id, db)
    return {"status": "success", "message": "Evaluation job re-queued and executed."}

@router.post("/stage-1/freeze")
def freeze_stage_1(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    result = freeze_stage1_and_qualify_top20(comp.id, db, admin.id)
    return result

@router.post("/stage-2/open")
def open_stage_2(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if comp:
        comp.current_stage = 2
        comp.status = "stage2_open"
        db.commit()
    return {"status": "success", "message": "Stage 2 is now open for qualified teams."}

@router.post("/final-results/freeze")
def freeze_final_results(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")
    result = freeze_final_and_select_top3(comp.id, db, admin.id)
    return result

@router.get("/rubrics")
def list_rubrics(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    rubrics = db.query(RubricVersion).order_by(RubricVersion.created_at.desc()).all()
    return [
        {
            "id": r.id,
            "stage": r.stage,
            "version": r.version,
            "rubric_json": r.rubric_json,
            "is_locked": r.is_locked,
            "created_at": r.created_at
        } for r in rubrics
    ]

@router.post("/rubrics")
def create_rubric(payload: RubricSchema, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    comp = db.query(Competition).first()
    if not comp:
        raise HTTPException(status_code=400, detail="No active competition.")

    rubric_obj = RubricVersion(
        competition_id=comp.id,
        version=payload.version,
        stage=payload.stage,
        rubric_json=payload.model_dump(),
        is_locked=True,
        created_by=admin.id
    )
    db.add(rubric_obj)
    db.commit()
    return {"status": "success", "id": rubric_obj.id, "version": rubric_obj.version}

@router.get("/audit-logs")
def get_audit_logs(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    out = []
    for l in logs:
        out.append({
            "id": l.id,
            "actor_id": l.actor_user_id,
            "actor_email": l.actor.email if l.actor else "system",
            "action": l.action,
            "entity_type": l.entity_type,
            "entity_id": l.entity_id,
            "details": l.details_json,
            "created_at": l.created_at
        })
    return out

@router.get("/exports/results")
def export_results_csv(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Exports official competition results as CSV with spreadsheet formula injection protection."""
    teams = db.query(Team).order_by(Team.final_score.desc(), Team.stage1_score.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow(["Rank", "Team Code", "Team Name", "Stage 1 Score", "Stage 2 Score", "Final Score", "Qualification Status"])
    
    def sanitize(val: Any) -> str:
        s = str(val or "")
        # Prevent formula injection
        if s and s[0] in ["=", "+", "-", "@", "\t", "\r"]:
            return f"'{s}"
        return s

    for idx, t in enumerate(teams, 1):
        writer.writerow([
            idx,
            sanitize(t.team_code),
            sanitize(t.team_name),
            t.stage1_score,
            t.stage2_score,
            t.final_score,
            sanitize(t.qualification_status)
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=AgentScore_Official_Results.csv"}
    )
