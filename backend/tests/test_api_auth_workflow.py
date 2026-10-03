import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.seed_data import seed_database
from app.db.session import SessionLocal
from app.models.models import User, Team, Competition

@pytest.fixture(scope="module")
def client():
    seed_database()
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_admin_login(client):
    response = client.post("/api/auth/login", json={
        "identifier": "admin@agentscore.org",
        "password": "AdminSecret2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "admin"

def test_team_leader_login(client):
    response = client.post("/api/auth/login", json={
        "identifier": "team_01",
        "password": "Team01Pass2026!"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "team_leader"
    assert data["team_code"] == "team_01"

def test_50_teams_seeded(client):
    db = SessionLocal()
    count = db.query(Team).count()
    db.close()
    assert count == 50

def test_public_leaderboard(client):
    response = client.get("/api/leaderboard/public")
    assert response.status_code == 200
    data = response.json()
    assert "entries" in data
    assert len(data["entries"]) > 0

def test_admin_dashboard_stats(client):
    login_resp = client.post("/api/auth/login", json={
        "identifier": "admin@agentscore.org",
        "password": "AdminSecret2026!"
    })
    token = login_resp.json()["access_token"]
    
    dash_resp = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert dash_resp.status_code == 200
    data = dash_resp.json()
    assert data["total_teams"] == 50

def test_stage1_freeze_qualifies_top20(client):
    login_resp = client.post("/api/auth/login", json={
        "identifier": "admin@agentscore.org",
        "password": "AdminSecret2026!"
    })
    token = login_resp.json()["access_token"]
    
    freeze_resp = client.post("/api/admin/stage-1/freeze", headers={"Authorization": f"Bearer {token}"})
    assert freeze_resp.status_code == 200
    data = freeze_resp.json()
    assert data["status"] == "success"
    assert data["qualified_teams_count"] == 20
