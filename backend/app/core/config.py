import os
from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AgentScore Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "agentscore_super_secret_jwt_key_university_2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    DATABASE_URL: str = "sqlite:///./agentscore.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    STORAGE_BASE_DIR: str = os.path.join(os.getcwd(), "storage")
    MAX_UPLOAD_SIZE_MB: int = 50
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # Competition Defaults
    STAGE1_ACCURACY_WEIGHT: float = 0.40
    STAGE1_TOOL_WEIGHT: float = 0.20
    STAGE1_CONSTRAINT_WEIGHT: float = 0.15
    STAGE1_QUALITY_WEIGHT: float = 0.15
    STAGE1_EFFICIENCY_WEIGHT: float = 0.10
    
    # Stage 2 Execution
    STAGE2_REQUEST_TIMEOUT_SECONDS: float = 10.0
    STAGE2_MAX_CONCURRENCY: int = 5
    STAGE2_REPEATED_RUNS: int = 3
    ENABLE_SSRF_PROTECTION: bool = True

    # --- Evaluation hardening (new) ---
    EVALUATOR_VERSION: str = "2.0.0"            # bump whenever scoring logic changes
    EVALUATE_INLINE: bool = True                # True: score inside the request (dev). False: worker only (prod)
    STAGE1_SCORE_POLICY: str = "best"           # "best" or "last"
    GROUND_TRUTH_PATH: str = ""                 # private Stage-1 labels; REQUIRED in production
    STAGE2_SUITE_PATH: str = ""                 # private Stage-2 task suite JSON; REQUIRED in production
    STAGE2_REQUIRE_HTTPS: bool = True
    STAGE2_ALLOW_LOCALHOST_DEV: bool = False    # dev-only (mock agent); ignored by the evaluator in production
    STAGE2_MAX_RESPONSE_BYTES: int = 1048576
    STAGE2_TOTAL_BUDGET_SECONDS: float = 150.0
    STAGE1_MAX_ROWS: int = 10000
    MAX_SUBMISSIONS_PER_TEAM_STAGE1: int = 10   # [ORGANISER DECISION] 0 = unlimited (not recommended: score oracle)
    MAX_SUBMISSIONS_PER_TEAM_STAGE2: int = 5    # [ORGANISER DECISION]
    PUBLIC_PROVISIONAL_LEADERBOARD: bool = True # False in production: live scores derive from private labels
    AUTO_PUBLISH_SNAPSHOTS: bool = True         # False in production: freeze -> admin approve -> publish
    JOB_LEASE_SECONDS: int = 600                # a job 'evaluating' longer than this is considered crashed
    JOB_MAX_ATTEMPTS: int = 3
    SEED_DEMO_DATA: bool = True                 # must be False in production
    
    @model_validator(mode="after")
    def _fail_closed_in_production(self):
        """Refuse to boot in production with unsafe defaults."""
        if self.ENVIRONMENT.lower() != "production":
            return self
        problems = []
        if len(self.SECRET_KEY) < 32 or "change" in self.SECRET_KEY.lower() or self.SECRET_KEY.startswith("agentscore_super"):
            problems.append("SECRET_KEY is default/weak")
        if self.DEBUG: problems.append("DEBUG must be False")
        if "sqlite" in self.DATABASE_URL: problems.append("SQLite is not allowed (use PostgreSQL)")
        if any("localhost" in o or "127.0.0.1" in o for o in self.cors_origin_list): problems.append("CORS_ORIGINS contains localhost")
        if self.PUBLIC_PROVISIONAL_LEADERBOARD: problems.append("PUBLIC_PROVISIONAL_LEADERBOARD must be False")
        if self.AUTO_PUBLISH_SNAPSHOTS: problems.append("AUTO_PUBLISH_SNAPSHOTS must be False")
        if self.ACCESS_TOKEN_EXPIRE_MINUTES > 240: problems.append("ACCESS_TOKEN_EXPIRE_MINUTES must be <= 240")
        if self.SEED_DEMO_DATA: problems.append("SEED_DEMO_DATA must be False")
        if self.EVALUATE_INLINE: problems.append("EVALUATE_INLINE must be False (use the worker)")
        if not self.GROUND_TRUTH_PATH: problems.append("GROUND_TRUTH_PATH not set")
        if not self.STAGE2_SUITE_PATH: problems.append("STAGE2_SUITE_PATH not set")
        if self.STAGE2_ALLOW_LOCALHOST_DEV: problems.append("STAGE2_ALLOW_LOCALHOST_DEV must be False")
        if not self.STAGE2_REQUIRE_HTTPS: problems.append("STAGE2_REQUIRE_HTTPS must be True")
        if problems:
            raise ValueError("Unsafe production configuration: " + "; ".join(problems))
        return self

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
