"""
FastAPI & SQLite API-level tests for AgentScore Hardening & Security Blueprint.
Tests Auth, RBAC/Isolation, Deadlines & State Machine, Upload Validation, Label Oracle Elimination,
Job Claiming/Reaping, Freeze & Snapshots Approval Workflow, Preflight Checks, and Production Settings.
"""
import io
import os
import time
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure low iterations in test runs
os.environ["PASSWORD_HASH_ITERATIONS"] = "20000"

from app.core.config import Settings, settings
from app.core.passwords import hash_password
from app.core.ratelimit import login_throttle
from app.core.security import create_access_token, get_password_hash
from app.db.session import Base, get_db
from app.main import app
from app.models.models import (
    AuditLog, Competition, EvaluationJob, EvaluationResult,
    LeaderboardSnapshot, QualificationSnapshot, RubricVersion,
    Submission, TaskResult, Team, TeamMember, User
)
from app.services.evaluation_service import process_evaluation_job
from app.services.preflight import run_preflight
from app.workers.evaluation_worker import reap_stale_jobs


class ApiHardeningTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        # Recreate schema for isolated test state
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.db = self.TestingSessionLocal()

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Clear login throttle cache
        login_throttle._fails.clear()
        login_throttle._locked_until.clear()

        # Seed initial test environment
        self._seed_test_data()

    def tearDown(self):
        self.db.close()
        app.dependency_overrides.clear()

    def _seed_test_data(self):
        # Create Admin
        self.admin_user = User(
            email="admin@agentscore.org",
            hashed_password=get_password_hash("AdminPass2026!"),
            role="admin",
            is_active=True
        )
        self.db.add(self.admin_user)

        # Create Team 1 (Leader + Team)
        self.t1_leader = User(
            email="leader1@team1.org",
            hashed_password=get_password_hash("Team01Pass2026!"),
            role="team_leader",
            is_active=True
        )
        self.db.add(self.t1_leader)
        self.db.flush()

        self.team1 = Team(
            team_code="team_01",
            team_name="Team Alpha",
            leader_user_id=self.t1_leader.id,
            qualification_status="registered",
            stage1_score=0.0
        )
        self.db.add(self.team1)

        # Create Team 2 (Leader + Team)
        self.t2_leader = User(
            email="leader2@team2.org",
            hashed_password=get_password_hash("Team02Pass2026!"),
            role="team_leader",
            is_active=True
        )
        self.db.add(self.t2_leader)
        self.db.flush()

        self.team2 = Team(
            team_code="team_02",
            team_name="Team Beta",
            leader_user_id=self.t2_leader.id,
            qualification_status="registered",
            stage1_score=0.0
        )
        self.db.add(self.team2)

        # Active Competition
        now = datetime.now(timezone.utc)
        self.comp = Competition(
            name="18-Hour AI Agent Competition",
            title="18-Hour AI Agent Competition",
            description="Autonomous multi-step agents",
            current_stage=1,
            status="active",
            start_time=now - timedelta(hours=1),
            stage_1_deadline=now + timedelta(hours=5),
            stage_2_deadline=now + timedelta(hours=10)
        )
        self.db.add(self.comp)

        # Stage 1 Rubric
        self.rubric1 = RubricVersion(
            stage=1,
            version="v1.0.0",
            rubric_json={
                "version": "v1.0.0",
                "weight_accuracy": 0.40,
                "weight_tool": 0.20,
                "weight_constraint": 0.15,
                "weight_quality": 0.15,
                "weight_efficiency": 0.10,
                "score_mode": "measured"
            },
            is_locked=True,
            created_by_user_id=self.admin_user.id
        )
        self.db.add(self.rubric1)

        self.db.commit()

        # Generate tokens
        self.admin_token = create_access_token({"sub": self.admin_user.id, "role": "admin", "email": self.admin_user.email, "tv": 0})
        self.team1_token = create_access_token({"sub": self.t1_leader.id, "role": "team_leader", "email": self.t1_leader.email, "tv": 0})
        self.team2_token = create_access_token({"sub": self.t2_leader.id, "role": "team_leader", "email": self.t2_leader.email, "tv": 0})

    def _auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    # =========================================================================
    # 1. Auth & Throttling
    # =========================================================================
    def test_auth_wrong_password_and_unknown_user_same_error(self):
        r1 = self.client.post("/api/auth/login", json={"identifier": "unknown@domain.com", "password": "AnyPassword123!"})
        r2 = self.client.post("/api/auth/login", json={"identifier": "leader1@team1.org", "password": "WrongPassword123!"})
        self.assertEqual(r1.status_code, 401)
        self.assertEqual(r2.status_code, 401)
        self.assertEqual(r1.json()["detail"], r2.json()["detail"])

    def test_auth_lockout_after_failures_and_reset_on_success(self):
        # 5 failed attempts
        for _ in range(5):
            self.client.post("/api/auth/login", json={"identifier": "team_01", "password": "WrongPassword123!"})
        r = self.client.post("/api/auth/login", json={"identifier": "team_01", "password": "Team01Pass2026!"})
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r.headers)

        # Clear throttle for identifier
        login_throttle.record_success("id:team_01")
        login_throttle.record_success(f"ip:testclient")
        r_ok = self.client.post("/api/auth/login", json={"identifier": "team_01", "password": "Team01Pass2026!"})
        self.assertEqual(r_ok.status_code, 200)

    def test_auth_inactive_user_forbidden(self):
        self.t1_leader.is_active = False
        self.db.commit()
        r = self.client.post("/api/auth/login", json={"identifier": "leader1@team1.org", "password": "Team01Pass2026!"})
        self.assertEqual(r.status_code, 403)
        self.assertIn("inactive", r.json()["detail"].lower())

    def test_auth_logout_revokes_token(self):
        # Initially valid
        r1 = self.client.get("/api/auth/me", headers=self._auth(self.team1_token))
        self.assertEqual(r1.status_code, 200)

        # Logout
        r_logout = self.client.post("/api/auth/logout", headers=self._auth(self.team1_token))
        self.assertEqual(r_logout.status_code, 200)

        # Old token is now revoked (token_version bumped)
        r2 = self.client.get("/api/auth/me", headers=self._auth(self.team1_token))
        self.assertEqual(r2.status_code, 401)

    def test_auth_change_password(self):
        r_bad_curr = self.client.post(
            "/api/auth/change-password",
            json={"current_password": "WrongCurrent123!", "new_password": "NewValidPass2026!"},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r_bad_curr.status_code, 400)

        r_weak = self.client.post(
            "/api/auth/change-password",
            json={"current_password": "Team01Pass2026!", "new_password": "short"},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r_weak.status_code, 422)

        r_ok = self.client.post(
            "/api/auth/change-password",
            json={"current_password": "Team01Pass2026!", "new_password": "NewStrongPassword2026!"},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r_ok.status_code, 200)

        # Old token revoked
        self.assertEqual(self.client.get("/api/auth/me", headers=self._auth(self.team1_token)).status_code, 401)

        # Can log in with new password
        r_new_login = self.client.post("/api/auth/login", json={"identifier": "team_01", "password": "NewStrongPassword2026!"})
        self.assertEqual(r_new_login.status_code, 200)

    # =========================================================================
    # 2. RBAC & Team Isolation
    # =========================================================================
    def test_rbac_admin_routes_reject_team_tokens(self):
        r = self.client.get("/api/admin/dashboard/stats", headers=self._auth(self.team1_token))
        self.assertEqual(r.status_code, 403)
        r2 = self.client.get("/api/admin/preflight", headers=self._auth(self.team1_token))
        self.assertEqual(r2.status_code, 403)

    def test_admin_on_submissions_my_returns_empty_list(self):
        r = self.client.get("/api/submissions/my", headers=self._auth(self.admin_token))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_admin_submitting_stage1_rejected_gracefully(self):
        csv_file = io.BytesIO(b"task_id,predicted_label\npriv_001,healthy_ratio\n")
        r = self.client.post(
            "/api/submissions/stage-1",
            files={"file": ("sub.csv", csv_file, "text/csv")},
            headers=self._auth(self.admin_token)
        )
        self.assertEqual(r.status_code, 403)
        self.assertIn("Administrator", r.json()["detail"])

    def test_team_a_cannot_access_team_b_submission(self):
        # Create submission for Team 1
        sub1 = Submission(team_id=self.team1.id, stage=1, submission_version=1, status="completed", is_official=True)
        self.db.add(sub1)
        self.db.commit()

        # Team 2 requesting Team 1's submission -> 404 (not 403, preventing ID probing)
        r = self.client.get(f"/api/submissions/{sub1.id}/results", headers=self._auth(self.team2_token))
        self.assertEqual(r.status_code, 404)
        r_rep = self.client.get(f"/api/submissions/{sub1.id}/report", headers=self._auth(self.team2_token))
        self.assertEqual(r_rep.status_code, 404)

    # =========================================================================
    # 3. Deadlines, States & Timezone-Aware Handling (H1 Regression)
    # =========================================================================
    def test_deadline_enforcement_and_naive_vs_aware_handling(self):
        # Past deadline
        self.comp.stage_1_deadline = datetime.now(timezone.utc) - timedelta(minutes=5)
        self.db.commit()

        csv_file = io.BytesIO(b"task_id,predicted_label\npriv_001,healthy_ratio\n")
        r = self.client.post(
            "/api/submissions/stage-1",
            files={"file": ("sub.csv", csv_file, "text/csv")},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r.status_code, 403)
        self.assertIn("deadline has passed", r.json()["detail"])

    def test_stage_2_rejected_when_not_open_or_team_not_qualified(self):
        # Stage 2 is not open yet
        r = self.client.post(
            "/api/submissions/stage-2",
            json={"application_url": "https://api.myagent.example.com"},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r.status_code, 403)
        self.assertIn("Stage 2 is not open", r.json()["detail"])

        # Open Stage 2 but team not qualified
        self.comp.status = "stage2_open"
        self.comp.current_stage = 2
        self.team1.qualification_status = "eliminated"
        self.db.commit()

        r2 = self.client.post(
            "/api/submissions/stage-2",
            json={"application_url": "https://api.myagent.example.com"},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r2.status_code, 403)
        self.assertIn("qualified teams", r2.json()["detail"])

    # =========================================================================
    # 4. Upload Validation & Label Oracle
    # =========================================================================
    def test_upload_invalid_extension_rejected(self):
        r = self.client.post(
            "/api/submissions/stage-1",
            files={"file": ("sub.exe", io.BytesIO(b"bad content"), "application/octet-stream")},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r.status_code, 400)

    def test_upload_formula_injection_rejected(self):
        csv_bad = b"task_id,predicted_label\npriv_001,=cmd|' /C calc'!A0\n"
        r = self.client.post(
            "/api/submissions/stage-1",
            files={"file": ("sub.csv", io.BytesIO(csv_bad), "text/csv")},
            headers=self._auth(self.team1_token)
        )
        self.assertEqual(r.status_code, 400)
        self.assertIn("formula", r.json()["detail"].lower())

    def test_label_oracle_elimination_for_teams(self):
        # Create evaluation result with TaskResult rows
        sub = Submission(team_id=self.team1.id, stage=1, submission_version=1, status="completed")
        self.db.add(sub)
        self.db.flush()

        job = EvaluationJob(submission_id=sub.id, team_id=self.team1.id, stage=1, status="completed")
        self.db.add(job)
        self.db.flush()

        res = EvaluationResult(
            evaluation_job_id=job.id,
            submission_id=sub.id,
            team_id=self.team1.id,
            stage=1,
            evaluator_version="2.0.0",
            rubric_version="v1.0.0",
            total_score=80.0,
            task_success_rate=80.0,
            metrics_json={},
            score_breakdown_json={},
            result_status="passed"
        )
        self.db.add(res)
        self.db.flush()

        self.db.add(TaskResult(evaluation_result_id=res.id, task_id="priv_001", passed=True, latency_ms=10.0))
        self.db.add(TaskResult(evaluation_result_id=res.id, task_id="priv_002", passed=False, latency_ms=10.0, safe_error_category="incorrect_label"))
        self.db.commit()

        # Team viewing results -> task_results is empty, failure_summary is present
        r_team = self.client.get(f"/api/submissions/{sub.id}/results", headers=self._auth(self.team1_token))
        self.assertEqual(r_team.status_code, 200)
        body = r_team.json()
        self.assertEqual(body["task_results"], [])
        self.assertEqual(body["failure_summary"], {"incorrect_label": 1})

        # Admin viewing results -> task_results has per-task items
        r_admin = self.client.get(f"/api/submissions/{sub.id}/results", headers=self._auth(self.admin_token))
        self.assertEqual(r_admin.status_code, 200)
        self.assertEqual(len(r_admin.json()["task_results"]), 2)

    # =========================================================================
    # 5. Job Claiming, Exception Rollback & Reaper
    # =========================================================================
    def test_concurrent_evaluation_job_claim(self):
        sub = Submission(team_id=self.team1.id, stage=1, submission_version=1, status="queued")
        self.db.add(sub)
        self.db.flush()
        job = EvaluationJob(submission_id=sub.id, team_id=self.team1.id, stage=1, status="queued")
        self.db.add(job)
        self.db.commit()

        # Claim the job
        res1 = process_evaluation_job(job.id, self.db)
        # Second invocation should return None because it is already claimed/evaluating/completed
        res2 = process_evaluation_job(job.id, self.db)
        self.assertIsNone(res2)

    def test_reaper_stale_job_requeue_and_max_attempts(self):
        sub = Submission(team_id=self.team1.id, stage=1, submission_version=1, status="queued")
        self.db.add(sub)
        self.db.flush()
        # Job started 15 minutes ago (lease expired)
        stale_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        job = EvaluationJob(
            submission_id=sub.id,
            team_id=self.team1.id,
            stage=1,
            status="evaluating",
            started_at=stale_time,
            attempt_count=1,
            max_attempts=3
        )
        self.db.add(job)
        self.db.commit()

        # Run reaper
        count = reap_stale_jobs(self.db)
        self.assertEqual(count, 1)
        self.db.refresh(job)
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.attempt_count, 2)

        # Now test failure when max_attempts reached
        job.status = "evaluating"
        job.started_at = stale_time
        job.attempt_count = 3
        self.db.commit()

        reap_stale_jobs(self.db)
        self.db.refresh(job)
        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error_code, "lease_expired")

    # =========================================================================
    # 6. Freeze & Snapshot Workflow (Review -> Approve -> Publish)
    # =========================================================================
    def test_freeze_stage1_guard_blocks_duplicate_and_pending_jobs(self):
        # 1. Block freeze if pending jobs exist
        sub = Submission(team_id=self.team1.id, stage=1, submission_version=1, status="queued")
        self.db.add(sub)
        self.db.flush()
        job = EvaluationJob(submission_id=sub.id, team_id=self.team1.id, stage=1, status="queued")
        self.db.add(job)
        self.db.commit()

        r_pending = self.client.post("/api/admin/stage-1/freeze-and-qualify", headers=self._auth(self.admin_token))
        self.assertEqual(r_pending.status_code, 409)

        # Complete job
        job.status = "completed"
        sub.status = "completed"
        self.team1.stage1_score = 90.0
        self.db.commit()

        # Freeze stage 1
        r_freeze = self.client.post("/api/admin/stage-1/freeze-and-qualify", headers=self._auth(self.admin_token))
        self.assertEqual(r_freeze.status_code, 200)

        # Calling freeze again returns 409
        r_dup = self.client.post("/api/admin/stage-1/freeze-and-qualify", headers=self._auth(self.admin_token))
        self.assertEqual(r_dup.status_code, 409)

    def test_snapshot_approve_and_publish_lifecycle(self):
        # Create an unpublished snapshot
        snap = LeaderboardSnapshot(
            competition_id=self.comp.id,
            stage=1,
            snapshot_json=[{"rank": 1, "team_code": "team_01", "stage1_score": 90.0}],
            is_published=False
        )
        self.db.add(snap)
        self.db.commit()

        # Cannot publish without approval
        r_pub_early = self.client.post(f"/api/admin/snapshots/{snap.id}/publish", headers=self._auth(self.admin_token))
        self.assertEqual(r_pub_early.status_code, 409)

        # Approve snapshot
        r_app = self.client.post(f"/api/admin/snapshots/{snap.id}/approve", headers=self._auth(self.admin_token))
        self.assertEqual(r_app.status_code, 200)

        # Publish snapshot
        r_pub = self.client.post(f"/api/admin/snapshots/{snap.id}/publish", headers=self._auth(self.admin_token))
        self.assertEqual(r_pub.status_code, 200)

        # Public leaderboard now serves published snapshot
        r_lb = self.client.get("/api/leaderboard/public?stage=1")
        self.assertEqual(r_lb.status_code, 200)
        self.assertTrue(r_lb.json()["is_published"])
        self.assertEqual(len(r_lb.json()["entries"]), 1)

    # =========================================================================
    # 7. Preflight & Settings Production Fail-Closed
    # =========================================================================
    def test_preflight_endpoint(self):
        r = self.client.get("/api/admin/preflight", headers=self._auth(self.admin_token))
        self.assertEqual(r.status_code, 200)
        self.assertIn("ready", r.json())
        self.assertIn("checks", r.json())

    def test_production_settings_fail_closed(self):
        with self.assertRaises(ValueError) as ctx:
            Settings(
                ENVIRONMENT="production",
                SECRET_KEY="default_insecure_secret_key_123",
                DEBUG=True,
                DATABASE_URL="sqlite:///./test.db",
                SEED_DEMO_DATA=True
            )
        err = str(ctx.exception)
        self.assertIn("SECRET_KEY", err)
        self.assertIn("DEBUG", err)
        self.assertIn("SQLite", err)

    # =========================================================================
    # 8. Rubric Weight Sum Validation
    # =========================================================================
    def test_rubric_weights_validation_rejected_if_sum_not_one(self):
        r = self.client.post(
            "/api/admin/rubrics",
            json={
                "stage": 1,
                "version": "v2.0",
                "weight_accuracy": 0.50,
                "weight_tool": 0.20,
                "weight_constraint": 0.10,
                "weight_quality": 0.10,
                "weight_efficiency": 0.05, # Sum = 0.95 != 1.0
                "stage_1_ratio": 0.60,
                "stage_2_ratio": 0.40
            },
            headers=self._auth(self.admin_token)
        )
        self.assertEqual(r.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
