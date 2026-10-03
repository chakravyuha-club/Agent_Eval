from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
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
    role = Column(String(50), default="team_leader", nullable=False) # 'admin', 'team_leader'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    team = relationship("Team", back_populates="leader", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="actor")

class Team(Base):
    __tablename__ = "teams"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_code = Column(String(50), unique=True, index=True, nullable=False) # e.g. 'team_01'
    team_name = Column(String(255), nullable=False)
    leader_user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False)
    qualification_status = Column(String(50), default="pending", nullable=False) # 'pending', 'qualified', 'eliminated'
    
    stage1_score = Column(Float, default=0.0, nullable=False)
    stage2_score = Column(Float, default=0.0, nullable=False)
    final_score = Column(Float, default=0.0, nullable=False)
    stage1_rank = Column(Integer, nullable=True)
    final_rank = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    leader = relationship("User", back_populates="team")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="team", cascade="all, delete-orphan")
    evaluation_results = relationship("EvaluationResult", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    is_leader = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    team = relationship("Team", back_populates="members")

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(50), default="active", nullable=False) # 'active', 'frozen_stage1', 'stage2_open', 'completed'
    start_time = Column(DateTime, default=utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    stage_1_deadline = Column(DateTime, nullable=True)
    stage_2_deadline = Column(DateTime, nullable=True)
    current_stage = Column(Integer, default=1, nullable=False)
    configuration_version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    datasets = relationship("Dataset", back_populates="competition")
    submissions = relationship("Submission", back_populates="competition")
    announcements = relationship("Announcement", back_populates="competition")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False)
    dataset_name = Column(String(255), nullable=False)
    dataset_type = Column(String(50), nullable=False) # 'training', 'public_test', 'private_test', 'schema'
    storage_path = Column(String(500), nullable=False)
    schema_json = Column(JSON, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    competition = relationship("Competition", back_populates="datasets")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False)
    stage = Column(Integer, default=1, nullable=False) # 1 or 2
    submission_type = Column(String(50), default="file", nullable=False) # 'file', 'url'
    file_storage_path = Column(String(500), nullable=True)
    application_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    submission_version = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="submitted", nullable=False) # 'submitted', 'evaluating', 'completed', 'failed'
    submitted_at = Column(DateTime, default=utcnow, nullable=False)
    selected_for_evaluation = Column(Boolean, default=True, nullable=False)

    team = relationship("Team", back_populates="submissions")
    competition = relationship("Competition", back_populates="submissions")
    jobs = relationship("EvaluationJob", back_populates="submission", cascade="all, delete-orphan")
    results = relationship("EvaluationResult", back_populates="submission")

class EvaluationJob(Base):
    __tablename__ = "evaluation_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    stage = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="queued", nullable=False) # 'queued', 'evaluating', 'passed', 'failed', 'cancelled'
    attempt_count = Column(Integer, default=1, nullable=False)
    queued_at = Column(DateTime, default=utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_code = Column(String(100), nullable=True)
    error_summary = Column(Text, nullable=True)

    submission = relationship("Submission", back_populates="jobs")
    result = relationship("EvaluationResult", back_populates="job", uselist=False)

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_job_id = Column(String(36), ForeignKey("evaluation_jobs.id"), nullable=False)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    stage = Column(Integer, default=1, nullable=False)
    evaluator_version = Column(String(50), default="v1.0.0", nullable=False)
    rubric_version = Column(String(50), default="v1.0.0", nullable=False)
    
    total_score = Column(Float, default=0.0, nullable=False)
    task_success_rate = Column(Float, default=0.0, nullable=False)
    metrics_json = Column(JSON, nullable=False, default=dict)
    score_breakdown_json = Column(JSON, nullable=False, default=dict)
    result_status = Column(String(50), default="valid", nullable=False) # 'valid', 'provisional', 'frozen'
    created_at = Column(DateTime, default=utcnow, nullable=False)

    job = relationship("EvaluationJob", back_populates="result")
    submission = relationship("Submission", back_populates="results")
    team = relationship("Team", back_populates="evaluation_results")
    task_results = relationship("TaskResult", back_populates="evaluation_result", cascade="all, delete-orphan")

class TaskResult(Base):
    __tablename__ = "task_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_result_id = Column(String(36), ForeignKey("evaluation_results.id"), nullable=False)
    task_id = Column(String(100), nullable=False)
    run_number = Column(Integer, default=1, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)
    metric_values_json = Column(JSON, nullable=True)
    latency_ms = Column(Float, default=0.0, nullable=False)
    safe_error_category = Column(String(100), nullable=True)

    evaluation_result = relationship("EvaluationResult", back_populates="task_results")

class RubricVersion(Base):
    __tablename__ = "rubric_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False)
    version = Column(String(50), default="v1.0.0", nullable=False)
    stage = Column(Integer, default=1, nullable=False)
    rubric_json = Column(JSON, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    created_by = Column(String(36), nullable=False)

class QualificationSnapshot(Base):
    __tablename__ = "qualification_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False)
    team_id = Column(String(36), ForeignKey("teams.id"), nullable=False)
    stage = Column(Integer, default=1, nullable=False)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=False)
    qualified = Column(Boolean, default=False, nullable=False)
    snapshot_version = Column(Integer, default=1, nullable=False)
    frozen_at = Column(DateTime, default=utcnow, nullable=False)

class LeaderboardSnapshot(Base):
    __tablename__ = "leaderboard_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False)
    stage = Column(Integer, default=1, nullable=False)
    snapshot_json = Column(JSON, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    published_at = Column(DateTime, nullable=True)

class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    competition_id = Column(String(36), ForeignKey("competitions.id"), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    created_by = Column(String(255), default="Organizing Committee", nullable=False)
    published_at = Column(DateTime, default=utcnow, nullable=False)

    competition = relationship("Competition", back_populates="announcements")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    details_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    actor = relationship("User", back_populates="audit_logs")
