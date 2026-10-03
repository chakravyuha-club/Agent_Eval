import os
import shutil
from datetime import datetime, timedelta, timezone
from app.db.session import SessionLocal, engine, Base
from app.models.models import (
    User, Team, TeamMember, Competition, Dataset, RubricVersion,
    Announcement, Submission, EvaluationJob, EvaluationResult, TaskResult
)
from app.core.security import get_password_hash

def utcnow():
    return datetime.now(timezone.utc)

TEAM_NAMES = [
    "Neural Knights", "Prompt Pioneers", "Agentic Alpha", "Cognitive Core",
    "Transformer Titans", "LLM Mavericks", "DeepMind Dynamos", "AutoGPT Artisans",
    "Vector Vortex", "Semantic Seekers", "Hyperplane Heroes", "Gradient Guardians",
    "Synapse Squad", "Bayesian Builders", "Latent Logic", "Token Tacticians",
    "Context Crafters", "RAG Rangers", "Inference Innovators", "LangChain Legends",
    "Agentic Apex", "Algorithmic Aces", "Byte Brigade", "Code Cartel",
    "Data Drifters", "Echo Encoders", "Feature Forge", "GigaGPT Guild",
    "Heuristic Hawks", "IntelliSync", "Jupyter Juggernauts", "Kernel Kings",
    "Logic Luminaries", "Matrix Masters", "Nexus Neuro", "Omni Agents",
    "Paradigms Plus", "Quantum Query", "Reinforce Realm", "Supervised Stars",
    "Tensor Tribe", "Ubiquitous Unit", "Vision Vectors", "Waveform Wizards",
    "Xenon X", "Yielding Yields", "ZeroShot Zeniths", "Apex Automata",
    "Binary Brains", "Cybernetic Champions"
]

def seed_database():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Create or verify Admin User
        admin = db.query(User).filter(User.email == "admin@agentscore.org").first()
        if not admin:
            print("Creating Admin user (admin@agentscore.org)...")
            admin = User(
                email="admin@agentscore.org",
                hashed_password=get_password_hash("AdminSecret2026!"),
                role="admin",
                is_active=True
            )
            db.add(admin)
            db.flush()

        # 2. Create Competition
        comp = db.query(Competition).first()
        if not comp:
            print("Creating Competition: 18-Hour AI Agent Building Challenge...")
            now = utcnow()
            comp = Competition(
                name="AgentScore 2026 — 18-Hour AI Agent Challenge",
                description="Build, optimize, and deploy multi-dimensional AI agents evaluated on task success, tool reliability, safety, and operational latency.",
                status="active",
                start_time=now,
                stage_1_deadline=now + timedelta(hours=10),
                stage_2_deadline=now + timedelta(hours=18),
                current_stage=1,
                configuration_version=1
            )
            db.add(comp)
            db.flush()

            # Add Rubrics
            r1 = RubricVersion(
                competition_id=comp.id,
                version="v1.0.0",
                stage=1,
                rubric_json={
                    "weight_accuracy": 0.40,
                    "weight_tool": 0.20,
                    "weight_constraint": 0.15,
                    "weight_quality": 0.15,
                    "weight_efficiency": 0.10
                },
                is_locked=True,
                created_by=admin.id
            )
            r2 = RubricVersion(
                competition_id=comp.id,
                version="v1.0.0",
                stage=2,
                rubric_json={
                    "weight_stage2_tsr": 0.35,
                    "weight_stage2_outcome": 0.20,
                    "weight_stage2_reliability": 0.15,
                    "weight_stage2_tool": 0.10,
                    "weight_stage2_safety": 0.10,
                    "weight_stage2_efficiency": 0.10,
                    "stage_1_ratio": 0.60,
                    "stage_2_ratio": 0.40
                },
                is_locked=True,
                created_by=admin.id
            )
            db.add(r1)
            db.add(r2)

            # Add Announcements
            ann1 = Announcement(
                competition_id=comp.id,
                title="Welcome to the 18-Hour AI Agent Competition!",
                body="Stage 1 submission portal is now open. Download your training and public test datasets. Good luck!",
                created_by="Organizing Committee"
            )
            ann2 = Announcement(
                competition_id=comp.id,
                title="Stage 2 API Contract & Deployed Agent Guidelines",
                body="Qualified teams advancing to Stage 2 must expose standard GET /health and POST /predict endpoints conforming to the official API contract.",
                created_by="Organizing Committee"
            )
            db.add(ann1)
            db.add(ann2)

            # Add Datasets
            d1 = Dataset(
                competition_id=comp.id,
                dataset_name="Benchmark Training Dataset",
                dataset_type="training",
                storage_path="/datasets/sample_training.csv",
                version=1
            )
            d2 = Dataset(
                competition_id=comp.id,
                dataset_name="Stage 1 Public Test Dataset",
                dataset_type="public_test",
                storage_path="/datasets/sample_public_test.csv",
                version=1
            )
            db.add(d1)
            db.add(d2)

        # 3. Create 50 Pre-Registered Teams
        existing_teams_count = db.query(Team).count()
        if existing_teams_count < 50:
            print(f"Seeding 50 pre-registered teams...")
            storage_dir = os.path.join(os.getcwd(), "storage", "uploads")
            os.makedirs(storage_dir, exist_ok=True)

            sample_sub_path = os.path.join(os.getcwd(), "datasets", "sample_submission.csv")
            if not os.path.exists(sample_sub_path):
                sample_sub_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "datasets", "sample_submission.csv")

            for i in range(1, 51):
                t_code = f"team_{i:02d}"
                t_name = TEAM_NAMES[i - 1]
                leader_email = f"leader{i:02d}@{t_code}.edu"
                leader_pwd = f"Team{i:02d}Pass2026!"

                user = db.query(User).filter(User.email == leader_email).first()
                if not user:
                    user = User(
                        email=leader_email,
                        hashed_password=get_password_hash(leader_pwd),
                        role="team_leader",
                        is_active=True
                    )
                    db.add(user)
                    db.flush()

                team = db.query(Team).filter(Team.team_code == t_code).first()
                if not team:
                    team = Team(
                        team_code=t_code,
                        team_name=t_name,
                        leader_user_id=user.id,
                        qualification_status="pending",
                        stage1_score=0.0,
                        stage2_score=0.0,
                        final_score=0.0
                    )
                    db.add(team)
                    db.flush()

                    # Add 2-3 realistic members per team
                    db.add(TeamMember(team_id=team.id, name=f"Leader {t_name}", email=leader_email, is_leader=True))
                    db.add(TeamMember(team_id=team.id, name=f"Dev 1 ({t_name})", email=f"dev1@{t_code}.edu", is_leader=False))
                    if i % 2 == 0:
                        db.add(TeamMember(team_id=team.id, name=f"Dev 2 ({t_name})", email=f"dev2@{t_code}.edu", is_leader=False))

                    # Seed sample completed Stage 1 submissions for top 25 teams
                    if i <= 25 and os.path.exists(sample_sub_path):
                        dest_sub = os.path.join(storage_dir, f"{t_code}_stage1_v1.csv")
                        shutil.copyfile(sample_sub_path, dest_sub)

                        sub = Submission(
                            team_id=team.id,
                            stage=1,
                            file_storage_path=dest_sub,
                            submission_version=1,
                            status="completed",
                            is_official=True
                        )
                        db.add(sub)
                        db.flush()

                        # Calculated realistic baseline scores
                        base_score = round(96.0 - (i * 1.8), 2)
                        team.stage1_score = max(55.0, base_score)

                        job = EvaluationJob(
                            submission_id=sub.id,
                            team_id=team.id,
                            stage=1,
                            status="completed",
                            attempt_count=1,
                            queued_at=utcnow() - timedelta(minutes=60),
                            started_at=utcnow() - timedelta(minutes=59),
                            completed_at=utcnow() - timedelta(minutes=58)
                        )
                        db.add(job)
                        db.flush()

                        res = EvaluationResult(
                            evaluation_job_id=job.id,
                            submission_id=sub.id,
                            team_id=team.id,
                            stage=1,
                            evaluator_version="v1.0.0",
                            rubric_version="v1.0.0",
                            total_score=team.stage1_score,
                            task_success_rate=round(team.stage1_score * 0.98, 2),
                            metrics_json={
                                "accuracy": round(team.stage1_score * 0.95, 2),
                                "macro_f1": round(team.stage1_score * 0.94, 2),
                                "tool_accuracy": 92.0,
                                "constraint_compliance": 100.0,
                                "output_quality": 95.0,
                                "efficiency": 90.0
                            },
                            score_breakdown_json={
                                "accuracy_weighted": round(team.stage1_score * 0.38, 2),
                                "tool_weighted": 18.4,
                                "constraint_weighted": 15.0,
                                "quality_weighted": 14.25,
                                "efficiency_weighted": 9.0
                            },
                            result_status="valid"
                        )
                        db.add(res)
                        db.flush()

                        db.add(TaskResult(
                            evaluation_result_id=res.id,
                            task_id="priv_001",
                            run_number=1,
                            passed=True,
                            latency_ms=12.5
                        ))

        db.commit()
        print("Database successfully seeded with 50 teams, competition, and benchmark data!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
