"""
Background Evaluation Worker
Polls and processes queued evaluation jobs with bounded retries and graceful crash isolation.
"""
import time
import sys
import os
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.models import EvaluationJob
from app.services.evaluation_service import process_evaluation_job

def run_worker_loop():
    print("AgentScore Background Evaluation Worker started. Listening for jobs...")
    while True:
        db: Session = SessionLocal()
        try:
            # Find next queued job
            job = db.query(EvaluationJob).filter(EvaluationJob.status == "queued").order_by(EvaluationJob.queued_at.asc()).first()
            if job:
                print(f"[Worker] Picked up job {job.id} for team {job.team_id} (Stage {job.stage})...")
                process_evaluation_job(job.id, db)
                print(f"[Worker] Completed job {job.id}.")
            else:
                time.sleep(2) # Sleep when idle
        except Exception as e:
            print(f"[Worker Error] {str(e)}", file=sys.stderr)
            time.sleep(3)
        finally:
            db.close()

if __name__ == "__main__":
    run_worker_loop()
