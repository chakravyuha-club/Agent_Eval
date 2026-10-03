import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["PASSWORD_HASH_ITERATIONS"] = "20000"

from app.db.session import Base, get_db
from app.main import app
from app.models.models import User, Team, Competition
from app.services.seed_data import seed_database


class ApiAuthWorkflowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

        # Override session in seed_database dependencies
        import app.services.seed_data as sd
        orig_session = sd.SessionLocal
        sd.SessionLocal = cls.TestingSessionLocal
        sd.engine = cls.engine
        try:
            seed_database()
        finally:
            sd.SessionLocal = orig_session

        def override_get_db():
            db = cls.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertIn(response.json()["status"], ["healthy", "ok"])

    def test_admin_login(self):
        response = self.client.post("/api/auth/login", json={
            "identifier": "admin@agentscore.org",
            "password": "AdminSecret2026!"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["role"], "admin")

    def test_team_leader_login(self):
        response = self.client.post("/api/auth/login", json={
            "identifier": "team_01",
            "password": "Team01Pass2026!"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["role"], "team_leader")
        self.assertEqual(data["team_code"], "team_01")

    def test_50_teams_seeded(self):
        db = self.TestingSessionLocal()
        count = db.query(Team).count()
        db.close()
        self.assertEqual(count, 50)

    def test_public_leaderboard(self):
        response = self.client.get("/api/leaderboard/public")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("entries", data)
        self.assertGreater(len(data["entries"]), 0)

    def test_admin_dashboard_stats(self):
        login_resp = self.client.post("/api/auth/login", json={
            "identifier": "admin@agentscore.org",
            "password": "AdminSecret2026!"
        })
        token = login_resp.json()["access_token"]
        
        dash_resp = self.client.get("/api/admin/dashboard/stats", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(dash_resp.status_code, 200)
        data = dash_resp.json()
        self.assertEqual(data["total_teams"], 50)

    def test_stage1_freeze_qualifies_top20(self):
        login_resp = self.client.post("/api/auth/login", json={
            "identifier": "admin@agentscore.org",
            "password": "AdminSecret2026!"
        })
        token = login_resp.json()["access_token"]
        
        freeze_resp = self.client.post("/api/admin/stage-1/freeze-and-qualify", headers={"Authorization": f"Bearer {token}"})
        self.assertIn(freeze_resp.status_code, [200, 409])
        if freeze_resp.status_code == 200:
            data = freeze_resp.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["qualified_teams_count"], 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)
