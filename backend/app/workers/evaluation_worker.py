"""
Background evaluation worker.

  * claims jobs atomically (compare-and-set) - safe to run several workers
  * reaper: a job stuck in 'evaluating' past JOB_LEASE_SECONDS (worker crashed) is re-queued, or failed
    once `max_attempts` is reached - it can never stay 'evaluating' forever
  * graceful SIGTERM/SIGINT shutdown, heartbeat log line, backoff on infrastructure errors
Run:  python -m app.workers.evaluation_worker
"""
import logging
import signal
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.models import EvaluationJob, Submission
from app.services.evaluation_service import process_evaluation_job

log = logging.getLogger("agentscore.worker")
_running = True


def _stop(*_):
    global _running
    _running = False


def _utc_aware(dt: datetime) -> datetime:
    """Ensure aware UTC for comparisons."""
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def reap_stale_jobs(db: Session, now: datetime | None = None) -> int:
    """Re-queue (or fail) jobs whose lease expired. Returns number of jobs touched."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(seconds=settings.JOB_LEASE_SECONDS)
    jobs = db.query(EvaluationJob).filter(EvaluationJob.status == "evaluating").all()
    stale = [j for j in jobs if j.started_at and _utc_aware(j.started_at) < cutoff]
    for job in stale:
        if job.attempt_count >= (job.max_attempts or settings.JOB_MAX_ATTEMPTS):
            job.status, job.error_code = "failed", "lease_expired"
            job.error_summary = "Evaluation worker stopped responding; maximum attempts reached."
            job.completed_at = now
            sub = db.query(Submission).filter(Submission.id == job.submission_id).first()
            if sub:
                sub.status = "failed"
        else:
            job.status, job.started_at = "queued", None
            job.attempt_count += 1
    if stale:
        db.commit()
        log.warning("reaped %d stale job(s)", len(stale))
    return len(stale)


def next_queued_job_id(db: Session) -> str | None:
    job = db.query(EvaluationJob).filter(EvaluationJob.status == "queued").order_by(EvaluationJob.queued_at.asc()).first()
    return job.id if job else None


def run_worker_loop(poll_seconds: float = 2.0, reap_every: float = 30.0) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)
    except Exception:
        pass
    log.info("AgentScore worker started (lease=%ss, max_attempts=%s)", settings.JOB_LEASE_SECONDS, settings.JOB_MAX_ATTEMPTS)
    last_reap = 0.0
    while _running:
        db: Session = SessionLocal()
        try:
            if time.monotonic() - last_reap > reap_every:
                reap_stale_jobs(db)
                last_reap = time.monotonic()
            job_id = next_queued_job_id(db)
            if job_id:
                log.info("processing job %s", job_id)
                process_evaluation_job(job_id, db)  # claims atomically; returns None if another worker won
            else:
                time.sleep(poll_seconds)
        except Exception:
            log.exception("worker loop error")
            db.rollback()
            time.sleep(3)
        finally:
            db.close()
    log.info("worker stopped")


if __name__ == "__main__":
    run_worker_loop()
