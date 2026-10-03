from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# ==================== Auth Schemas ====================
class LoginRequest(BaseModel):
    identifier: str # Email or Team Code (e.g. 'team_01' or 'admin@agentscore.org')
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    email: str
    team_id: Optional[str] = None
    team_code: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    team_id: Optional[str] = None
    team_code: Optional[str] = None
    team_name: Optional[str] = None

# ==================== Team Schemas ====================
class TeamMemberSchema(BaseModel):
    name: str
    email: str
    is_leader: bool = False

class TeamCreateRequest(BaseModel):
    team_code: str
    team_name: str
    leader_email: EmailStr
    leader_password: str
    members: List[TeamMemberSchema] = []

class TeamUpdateRequest(BaseModel):
    team_name: Optional[str] = None
    qualification_status: Optional[str] = None # 'pending', 'qualified', 'eliminated'

class TeamMemberResponse(BaseModel):
    id: str
    name: str
    email: str
    is_leader: bool

class TeamResponse(BaseModel):
    id: str
    team_code: str
    team_name: str
    qualification_status: str
    stage1_score: float
    stage2_score: float
    final_score: float
    stage1_rank: Optional[int] = None
    final_rank: Optional[int] = None
    members: List[TeamMemberResponse] = []
    created_at: datetime

# ==================== Competition & Datasets ====================
class CompetitionResponse(BaseModel):
    id: str
    name: str
    description: str
    status: str
    start_time: datetime
    stage_1_deadline: Optional[datetime]
    stage_2_deadline: Optional[datetime]
    current_stage: int

class DatasetResponse(BaseModel):
    id: str
    dataset_name: str
    dataset_type: str
    storage_path: str
    schema_json: Optional[Dict[str, Any]] = None
    version: int
    created_at: datetime

class AnnouncementResponse(BaseModel):
    id: str
    title: str
    body: str
    created_by: str
    published_at: datetime

# ==================== Submissions & Jobs ====================
class Stage2SubmissionCreate(BaseModel):
    application_url: str
    notes: Optional[str] = None
    deployment_version: Optional[str] = "v1.0"
    confirmation_reviewed: bool = True

class SubmissionResponse(BaseModel):
    id: str
    team_id: str
    team_name: Optional[str] = None
    stage: int
    submission_type: str
    application_url: Optional[str] = None
    submission_version: int
    status: str
    submitted_at: datetime
    selected_for_evaluation: bool

class TaskResultResponse(BaseModel):
    task_id: str
    run_number: int = 1
    passed: bool
    latency_ms: float
    safe_error_category: Optional[str] = None

class EvaluationResultResponse(BaseModel):
    id: str
    evaluation_job_id: str
    submission_id: str
    team_id: str
    stage: int
    evaluator_version: str
    rubric_version: str
    total_score: float
    task_success_rate: float
    metrics: Dict[str, Any]
    score_breakdown: Dict[str, Any]
    result_status: str
    created_at: datetime
    task_results: List[TaskResultResponse] = []
    failure_summary: Optional[Dict[str, int]] = None

class EvaluationJobResponse(BaseModel):
    id: str
    submission_id: str
    team_id: str
    stage: int
    status: str
    attempt_count: int
    queued_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_summary: Optional[str] = None
    result: Optional[EvaluationResultResponse] = None

# ==================== Rubrics ====================
class RubricSchema(BaseModel):
    stage: int
    version: str = "v1.0.0"
    weight_accuracy: float = 0.40
    weight_tool: float = 0.20
    weight_constraint: float = 0.15
    weight_quality: float = 0.15
    weight_efficiency: float = 0.10
    
    # Stage 2 weights
    weight_stage2_tsr: float = 0.35
    weight_stage2_outcome: float = 0.20
    weight_stage2_reliability: float = 0.15
    weight_stage2_tool: float = 0.10
    weight_stage2_safety: float = 0.10
    weight_stage2_efficiency: float = 0.10

    stage_1_ratio: float = 0.60
    stage_2_ratio: float = 0.40

    @model_validator(mode="after")
    def validate_weights(self):
        if self.stage == 1:
            total = self.weight_accuracy + self.weight_tool + self.weight_constraint + self.weight_quality + self.weight_efficiency
            if abs(total - 1.0) > 1e-4:
                raise ValueError(f"Stage 1 rubric weights must sum to 1.0 (current sum: {round(total, 4)})")
        elif self.stage == 2:
            total = self.weight_stage2_tsr + self.weight_stage2_outcome + self.weight_stage2_reliability + self.weight_stage2_tool + self.weight_stage2_safety + self.weight_stage2_efficiency
            if abs(total - 1.0) > 1e-4:
                raise ValueError(f"Stage 2 rubric weights must sum to 1.0 (current sum: {round(total, 4)})")
        if abs((self.stage_1_ratio + self.stage_2_ratio) - 1.0) > 1e-4:
            raise ValueError("Competition stage ratios (stage_1_ratio + stage_2_ratio) must sum to 1.0")
        return self

# ==================== Leaderboard ====================
class LeaderboardEntry(BaseModel):
    rank: int
    team_id: str
    team_code: str
    team_name: str
    stage1_score: float
    stage2_score: Optional[float] = None
    final_score: Optional[float] = None
    qualification_status: str
    is_provisional: bool

class PublicLeaderboardResponse(BaseModel):
    stage: int
    is_published: bool
    last_updated: datetime
    entries: List[LeaderboardEntry]

# ==================== Admin Dashboard Stats ====================
class AdminDashboardStats(BaseModel):
    total_teams: int
    teams_submitted_stage1: int
    teams_submitted_stage2: int
    pending_evaluations: int
    completed_evaluations: int
    failed_evaluations: int
    qualified_teams_count: int
    competition_stage: int
    competition_status: str

class AuditLogResponse(BaseModel):
    id: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: Optional[str]
    details: Optional[Dict[str, Any]]
    created_at: datetime
