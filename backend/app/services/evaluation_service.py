import os
import io
import json
import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.models import (
    EvaluationJob, EvaluationResult, TaskResult, Submission, Team,
    Competition, RubricVersion, QualificationSnapshot, LeaderboardSnapshot, AuditLog
)
from evaluator.stage1.evaluator import validate_prediction_file, evaluate_stage1_submission
from evaluator.stage2.evaluator import evaluate_stage2_deployed_agent

logger = logging.getLogger("agentscore.evaluation")

def utcnow():
    return datetime.now(timezone.utc)

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

def load_ground_truth() -> pd.DataFrame:
    """Private Stage-1 labels. Production requires GROUND_TRUTH_PATH; labels are never synthesised in code."""
    path = settings.GROUND_TRUTH_PATH
    if not path:
        if settings.ENVIRONMENT.lower() == "production":
            raise FileNotFoundError("ground_truth_not_configured")
        path = os.path.join(_REPO_ROOT, "datasets", "sample_hidden_test.csv")  # DEV SAMPLE ONLY
    if not os.path.exists(path):
        raise FileNotFoundError("ground_truth_not_found")
    return pd.read_csv(path, dtype=str, keep_default_na=False)

def load_stage2_suite() -> list:
    """Private Stage-2 suite (tasks + assertions). Production requires STAGE2_SUITE_PATH."""
    path = settings.STAGE2_SUITE_PATH
    if not path:
        if settings.ENVIRONMENT.lower() == "production":
            raise FileNotFoundError("stage2_suite_not_configured")
        path = os.path.join(_REPO_ROOT, "datasets", "sample_stage2_suite.json")  # DEV SAMPLE ONLY
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def claim_job(db: Session, job_id: str) -> bool:
    """Atomic queued->evaluating compare-and-set so the API thread and worker never run the same job twice."""
    n = db.query(EvaluationJob).filter(EvaluationJob.id == job_id, EvaluationJob.status == "queued").update(
        {"status": "evaluating", "started_at": utcnow()}, synchronize_session=False)
    db.commit()
    return n == 1

def get_active_rubric(db: Session, stage: int) -> Dict[str, Any]:
    """Retrieves active rubric configuration for the given stage."""
    rubric_rec = db.query(RubricVersion).filter(RubricVersion.stage == stage).order_by(RubricVersion.created_at.desc()).first()
    if rubric_rec and rubric_rec.rubric_json:
        return rubric_rec.rubric_json
    
    # Fallback to default rubric parameters from config
    if stage == 1:
        return {
            "version": "default_v1",
            "weight_accuracy": settings.STAGE1_ACCURACY_WEIGHT,
            "weight_tool": settings.STAGE1_TOOL_WEIGHT,
            "weight_constraint": settings.STAGE1_CONSTRAINT_WEIGHT,
            "weight_quality": settings.STAGE1_QUALITY_WEIGHT,
            "weight_efficiency": settings.STAGE1_EFFICIENCY_WEIGHT,
            "score_mode": "measured"
        }
    else:
        return {
            "version": "default_v1",
            "weight_stage2_tsr": 0.35,
            "weight_stage2_outcome": 0.20,
            "weight_stage2_reliability": 0.15,
            "weight_stage2_tool": 0.10,
            "weight_stage2_safety": 0.10,
            "weight_stage2_efficiency": 0.10
        }

def process_evaluation_job(job_id: str, db: Session) -> Optional[EvaluationResult]:
    """
    Worker function to process an evaluation job asynchronously or synchronously.
    Handles job status updates, executes evaluation, saves results and updates team scores.
    """
    job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
    if not job:
        return None

    submission = db.query(Submission).filter(Submission.id == job.submission_id).first()
    team = db.query(Team).filter(Team.id == job.team_id).first()
    
    if not submission or not team:
        job.status = "failed"
        job.error_summary = "Missing associated submission or team record."
        job.completed_at = utcnow()
        db.commit()
        return None

    if not claim_job(db, job_id):
        return None  # already claimed / finished by another runner
    db.refresh(job)

    rubric = get_active_rubric(db, job.stage)

    try:
        if job.stage == 1:
            if not submission.file_storage_path or not os.path.exists(submission.file_storage_path):
                raise ValueError("Stage 1 submission file is missing on storage.")

            with open(submission.file_storage_path, "rb") as f:
                file_bytes = f.read()

            gt_df = load_ground_truth()
            expected_ids = set(gt_df["task_id"].astype(str).str.strip())
            is_valid, err_msg, sub_df = validate_prediction_file(
                file_bytes, submission.file_storage_path,
                expected_task_ids=expected_ids, max_rows=settings.STAGE1_MAX_ROWS)
            if not is_valid or sub_df is None:
                raise ValueError(err_msg or "Invalid prediction file format.")

            eval_output = evaluate_stage1_submission(sub_df, gt_df, rubric)

            eval_res = EvaluationResult(
                evaluation_job_id=job.id,
                submission_id=submission.id,
                team_id=team.id,
                stage=1,
                evaluator_version=settings.EVALUATOR_VERSION,
                rubric_version=str(rubric.get("version", "v1.0.0")),
                total_score=eval_output["total_score"],
                task_success_rate=eval_output["task_success_rate"],
                metrics_json=eval_output["metrics"],
                score_breakdown_json=eval_output["score_breakdown"],
                components_used_json=eval_output.get("components_used"),
                result_status="passed" if eval_output["total_score"] > 0 else "failed"
            )
            db.add(eval_res)
            db.flush()

            for t_res in eval_output["task_results"]:
                db.add(TaskResult(
                    evaluation_result_id=eval_res.id,
                    task_id=t_res["task_id"],
                    passed=t_res["passed"],
                    latency_ms=t_res["latency_ms"],
                    safe_error_category=t_res["error_category"]
                ))

            # Update team Stage 1 score according to policy
            if settings.STAGE1_SCORE_POLICY == "last":
                team.stage1_score = eval_output["total_score"]
            else:  # default: "best"
                team.stage1_score = max(team.stage1_score, eval_output["total_score"])

        elif job.stage == 2:
            app_url = submission.application_url
            if not app_url:
                raise ValueError("Stage 2 requires a valid deployed application URL.")

            test_suite = load_stage2_suite()

            eval_output = evaluate_stage2_deployed_agent(
                application_url=app_url,
                test_suite=test_suite,
                rubric=rubric,
                repeated_runs=settings.STAGE2_REPEATED_RUNS,
                timeout_seconds=settings.STAGE2_REQUEST_TIMEOUT_SECONDS,
                allow_localhost=settings.STAGE2_ALLOW_LOCALHOST_DEV,  # dev-only; evaluator forces False in production
                require_https=settings.STAGE2_REQUIRE_HTTPS,
                max_response_bytes=settings.STAGE2_MAX_RESPONSE_BYTES,
                total_budget_seconds=settings.STAGE2_TOTAL_BUDGET_SECONDS,
            )

            if not eval_output.get("success", False):
                job.status = "failed"
                job.error_code = eval_output.get("error_category", "evaluation_failed")
                job.error_summary = eval_output.get("error_summary", "Evaluation failed.")
                job.completed_at = utcnow()
                submission.status = "failed"
                db.commit()
                return None

            eval_res = EvaluationResult(
                evaluation_job_id=job.id,
                submission_id=submission.id,
                team_id=team.id,
                stage=2,
                evaluator_version=settings.EVALUATOR_VERSION,
                rubric_version=str(rubric.get("version", "v1.0.0")),
                total_score=eval_output["total_score"],
                task_success_rate=eval_output["task_success_rate"],
                metrics_json=eval_output["metrics"],
                score_breakdown_json=eval_output["score_breakdown"],
                result_status="passed"
            )
            db.add(eval_res)
            db.flush()

            for t_res in eval_output["task_results"]:
                db.add(TaskResult(
                    evaluation_result_id=eval_res.id,
                    task_id=t_res["task_id"],
                    passed=t_res["passed"],
                    latency_ms=t_res["latency_ms"],
                    safe_error_category=t_res["error_category"]
                ))

            # Update team Stage 2 and Final Score
            team.stage2_score = eval_output["total_score"]
            team.final_score = round((team.stage1_score * 0.60) + (team.stage2_score * 0.40), 2)

        # Mark job and submission completed
        job.status = "completed"
        job.completed_at = utcnow()
        submission.status = "completed"
        db.commit()
        db.refresh(eval_res)
        return eval_res

    except Exception as e:
        db.rollback()  # session may be in a failed state (e.g. after a flush error)
        logger.exception("Evaluation job %s failed", job_id)
        job = db.query(EvaluationJob).filter(EvaluationJob.id == job_id).first()
        submission = db.query(Submission).filter(Submission.id == job.submission_id).first() if job else None
        if job:
            job.status = "failed"
            job.error_code = "runtime_exception"
            job.error_summary = f"{type(e).__name__}: {str(e)[:200]}"  # admin-only; full trace is in logs
            job.completed_at = utcnow()
        if submission:
            submission.status = "failed"
        db.commit()
        return None

class StateError(Exception):
    """Raised when an admin action is invalid for the current competition state (mapped to HTTP 409)."""

def _pending_jobs(db: Session, stage: int) -> int:
    return db.query(EvaluationJob).filter(EvaluationJob.stage == stage, EvaluationJob.status.in_(["queued", "evaluating"])).count()

def freeze_stage1_and_qualify_top20(competition_id: str, db: Session, user_id: str) -> Dict[str, Any]:
    """
    Ranks teams by Stage 1 score, qualifies the top 20 teams into Stage 2,
    marks remaining as eliminated, and locks Stage 1 results into a snapshot.
    """
    comp0 = db.query(Competition).filter(Competition.id == competition_id).first()
    if not comp0 or comp0.status != "active" or comp0.current_stage != 1:
        raise StateError("Stage 1 can only be frozen once, while the competition is in the active Stage 1 state.")
    pending = _pending_jobs(db, 1)
    if pending:
        raise StateError(f"{pending} Stage 1 evaluation job(s) are still queued/running; wait or cancel them before freezing.")

    teams = db.query(Team).order_by(Team.stage1_score.desc(), Team.created_at.asc()).all()
    cutoff_tie = len(teams) > 20 and teams[19].stage1_score == teams[20].stage1_score and teams[19].stage1_score > 0

    qualified_count = 0
    snapshot_data = []

    for rank, team in enumerate(teams, start=1):
        team.rank_stage1 = rank
        if rank <= 20 and team.stage1_score > 0:
            team.qualification_status = "qualified"
            qualified_count += 1
        else:
            team.qualification_status = "eliminated"

        snapshot_data.append({
            "rank": rank,
            "team_id": team.id,
            "team_code": team.team_code,
            "team_name": team.team_name,
            "stage1_score": team.stage1_score,
            "qualification_status": team.qualification_status
        })

    # Update competition state
    comp0.status = "frozen_stage1"

    # Create Qualification Snapshot
    qual_snap = QualificationSnapshot(
        competition_id=competition_id,
        snapshot_data_json=snapshot_data,
        frozen_by_user_id=user_id,
        frozen_at=utcnow()
    )
    db.add(qual_snap)

    # Create Leaderboard Snapshot
    lb_snap = LeaderboardSnapshot(
        competition_id=competition_id,
        stage=1,
        snapshot_json=snapshot_data,
        is_published=settings.AUTO_PUBLISH_SNAPSHOTS,
        published_at=utcnow() if settings.AUTO_PUBLISH_SNAPSHOTS else None
    )
    db.add(lb_snap)

    # Audit Log
    audit = AuditLog(
        actor_user_id=user_id,
        action="FREEZE_STAGE1_QUALIFY_TOP20",
        entity_type="Competition",
        entity_id=competition_id,
        details_json={"qualified_teams": qualified_count, "total_ranked": len(teams), "cutoff_tie": bool(cutoff_tie)}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "qualified_teams_count": qualified_count,
        "total_teams": len(teams),
        "snapshot_created": True,
        "cutoff_tie": bool(cutoff_tie)  # True => rank 20/21 share a score; tie-break policy needs an organiser ruling
    }

def freeze_final_and_select_top3(competition_id: str, db: Session, user_id: str) -> Dict[str, Any]:
    """
    Ranks qualified teams by composite Final Score (60% Stage 1 + 40% Stage 2),
    locks final results, and selects the Top 3 Winners.
    """
    comp0 = db.query(Competition).filter(Competition.id == competition_id).first()
    if not comp0 or comp0.status != "stage2_open":
        raise StateError("Final results can only be frozen once, while Stage 2 is open.")
    pending = _pending_jobs(db, 2)
    if pending:
        raise StateError(f"{pending} Stage 2 evaluation job(s) are still queued/running.")

    teams = db.query(Team).filter(Team.qualification_status == "qualified").order_by(
        Team.final_score.desc(),
        Team.stage2_score.desc(),
        Team.stage1_score.desc(),
        Team.created_at.asc()
    ).all()

    snapshot_data = []
    for rank, team in enumerate(teams, start=1):
        team.rank_final = rank
        snapshot_data.append({
            "rank": rank,
            "team_id": team.id,
            "team_code": team.team_code,
            "team_name": team.team_name,
            "stage1_score": team.stage1_score,
            "stage2_score": team.stage2_score,
            "final_score": team.final_score,
            "is_winner": (rank <= 3)
        })

    # Update competition state
    comp0.status = "completed"

    # Create Final Leaderboard Snapshot
    lb_snap = LeaderboardSnapshot(
        competition_id=competition_id,
        stage=2,
        snapshot_json=snapshot_data,
        is_published=settings.AUTO_PUBLISH_SNAPSHOTS,
        published_at=utcnow() if settings.AUTO_PUBLISH_SNAPSHOTS else None
    )
    db.add(lb_snap)

    # Audit Log
    audit = AuditLog(
        actor_user_id=user_id,
        action="FREEZE_FINAL_SELECT_TOP3",
        entity_type="Competition",
        entity_id=competition_id,
        details_json={"winner_count": min(3, len(teams)), "ranked_teams": len(teams)}
    )
    db.add(audit)
    db.commit()

    return {
        "status": "success",
        "top3_teams": snapshot_data[:3],
        "total_ranked": len(teams),
        "snapshot_created": True
    }
