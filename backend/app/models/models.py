import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey,
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.db.session import Base

def generate_uuid():
    return str(uuid.uuid4())

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="team_leader", nullable=False) # 'admin', 'team_leader', 'member'
    is_active = Column(Boolean, default=True, nullable=False)
    token_version = Column(Integer, default=0, nullable=False)  # bump to revoke all issued JWTs
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    team = relationship("Team", back_populates="leader", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="actor")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'team_leader', 'member')", name="chk_user_role"),
    )

class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_code = Column(String(50), unique=True, index=True, nullable=False)
    team_name = Column(String(255), nullable=False)
    leader_user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    qualification_status = Column(String(50), default="registered", nullable=False) # 'registered', 'qualified', 'eliminated'
    stage1_score = Column(Float, default=0.0, nullable=False)
    stage2_score = Column(Float, default=0.0, nullable=False)
    final_score = Column(Float, default=0.0, nullable=False)
    rank_stage1 = Column(Integer, nullable=True)
    rank_final = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    leader = relationship("User", back_populates="team")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="team", cascade="all, delete-orphan")
    evaluation_results = relationship("EvaluationResult", back_populates="team")

    __table_args__ = (
        CheckConstraint("qualification_status IN ('registered', 'pending', 'qualified', 'eliminated')", name="chk_team_qual_status"),
    )

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    is_leader = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    team = relationship("Team", back_populates="members")

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False, default="AgentScore Competition")
    title = Column(String(255), nullable=False, default="AgentScore Competition")
    description = Column(Text, nullable=True)
    current_stage = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="active", nullable=False) # 'draft', 'active', 'frozen_stage1', 'stage2_open', 'frozen_final', 'completed'
    configuration_version = Column(Integer, default=1, nullable=False)
    start_time = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    stage_1_deadline = Column(DateTime(timezone=True), nullable=True)
    stage_2_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("current_stage IN (1, 2)", name="chk_competition_stage"),
        CheckConstraint("status IN ('draft', 'active', 'frozen_stage1', 'stage2_open', 'frozen_final', 'completed')", name="chk_competition_status"),
    )

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=True, index=True)
    dataset_name = Column(String(255), nullable=False)
    dataset_type = Column(String(50), nullable=False) # 'training', 'public_test', 'private_test', 'schema'
    storage_path = Column(String(1024), nullable=False)
    schema_json = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    created_by = Column(String(255), default="System Organizer", nullable=False)
    published_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(Integer, nullable=False) # 1 or 2
    submission_version = Column(Integer, default=1, nullable=False)
    file_storage_path = Column(String(1024), nullable=True)
    application_url = Column(String(1024), nullable=True)
    status = Column(String(50), default="queued", nullable=False, index=True) # 'queued', 'evaluating', 'completed', 'failed'
    is_official = Column(Boolean, default=True, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    team = relationship("Team", back_populates="submissions")
    jobs = relationship("EvaluationJob", back_populates="submission", cascade="all, delete-orphan")
    result = relationship("EvaluationResult", back_populates="submission", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("team_id", "stage", "submission_version", name="uq_team_stage_submission_version"),
        CheckConstraint("stage IN (1, 2)", name="chk_submission_stage"),
        CheckConstraint("status IN ('queued', 'evaluating', 'completed', 'failed')", name="chk_submission_status"),
        Index("idx_submissions_team_stage", "team_id", "stage"),
    )

class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(Integer, nullable=False)
    status = Column(String(50), default="queued", nullable=False, index=True) # 'queued', 'evaluating', 'completed', 'failed'
    attempt_count = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    queued_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(100), nullable=True)
    error_summary = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="jobs")
    result = relationship("EvaluationResult", back_populates="job", uselist=False)

    __table_args__ = (
        CheckConstraint("stage IN (1, 2)", name="chk_job_stage"),
        CheckConstraint("status IN ('queued', 'evaluating', 'completed', 'failed')", name="chk_job_status"),
        Index("idx_eval_jobs_status_queued_at", "status", "queued_at"),
    )

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_job_id = Column(String(36), ForeignKey("evaluation_jobs.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    team_id = Column(String(36), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(Integer, nullable=False)
    evaluator_version = Column(String(50), nullable=False)
    rubric_version = Column(String(50), nullable=False)
    ruleset_hash = Column(String(64), nullable=True)
    seed = Column(String(64), nullable=True)
    is_official = Column(Boolean, default=True, nullable=False)
    total_score = Column(Float, nullable=False)
    task_success_rate = Column(Float, nullable=False)
    metrics_json = Column(JSON, nullable=False)
    score_breakdown_json = Column(JSON, nullable=False)
    components_used_json = Column(JSON, nullable=True)
    result_status = Column(String(50), default="passed", nullable=False) # 'passed', 'failed', 'error'
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    job = relationship("EvaluationJob", back_populates="result")
    submission = relationship("Submission", back_populates="result")
    team = relationship("Team", back_populates="evaluation_results")
    task_results = relationship("TaskResult", back_populates="evaluation_result", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("stage IN (1, 2)", name="chk_result_stage"),
        CheckConstraint("result_status IN ('passed', 'failed', 'error', 'valid')", name="chk_result_status"),
    )

class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_result_id = Column(String(36), ForeignKey("evaluation_results.id", ondelete="CASCADE"), nullable=False, index=True)
    task_id = Column(String(100), nullable=False, index=True)
    run_number = Column(Integer, default=1, nullable=False)
    passed = Column(Boolean, nullable=False)
    latency_ms = Column(Float, default=0.0, nullable=False)
    safe_error_category = Column(String(100), nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    evaluation_result = relationship("EvaluationResult", back_populates="task_results")

class RubricVersion(Base):
    __tablename__ = "rubric_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=True, index=True)
    stage = Column(Integer, nullable=False)
    version = Column(String(50), nullable=False)
    rubric_json = Column(JSON, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("stage IN (1, 2)", name="chk_rubric_stage"),
    )

    def __init__(self, **kwargs):
        if "created_by" in kwargs and "created_by_user_id" not in kwargs:
            kwargs["created_by_user_id"] = kwargs.pop("created_by")
        super().__init__(**kwargs)

class QualificationSnapshot(Base):
    __tablename__ = "qualification_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False, index=True)
    snapshot_data_json = Column(JSON, nullable=False)
    frozen_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    frozen_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

class LeaderboardSnapshot(Base):
    __tablename__ = "leaderboard_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False, index=True)
    stage = Column(Integer, default=1, nullable=False)
    snapshot_json = Column(JSON, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    approved_by = Column(String(36), nullable=True)      # admin user id; publication requires approval
    approved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("stage IN (1, 2)", name="chk_snapshot_stage"),
    )

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(36), nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    actor = relationship("User", back_populates="audit_logs")
