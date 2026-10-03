import csv
import io
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.models import User, Team, TeamMember, AuditLog
from app.core.security import get_password_hash

def bulk_import_teams_from_csv(csv_content: str, db: Session, admin_user_id: str) -> Tuple[int, List[str]]:
    """
    Imports teams from a CSV file.
    Expected CSV columns: team_code,team_name,leader_name,leader_email,leader_password,member2_name,member2_email,member3_name,member3_email
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    imported_count = 0
    errors = []

    for row_idx, row in enumerate(reader, start=1):
        try:
            team_code = str(row.get("team_code", "")).strip().lower()
            team_name = str(row.get("team_name", "")).strip()
            leader_email = str(row.get("leader_email", "")).strip().lower()
            leader_name = str(row.get("leader_name", "")).strip() or f"{team_name} Leader"
            leader_pwd = str(row.get("leader_password", "")).strip() or f"{team_code}Pass2026!"

            if not team_code or not team_name or not leader_email:
                errors.append(f"Row {row_idx}: Missing required fields (team_code, team_name, or leader_email).")
                continue

            # Check if user or team already exists
            existing_user = db.query(User).filter(User.email == leader_email).first()
            existing_team = db.query(Team).filter(Team.team_code == team_code).first()

            if existing_team or existing_user:
                errors.append(f"Row {row_idx}: Team '{team_code}' or Email '{leader_email}' already exists.")
                continue

            # Create User
            user = User(
                email=leader_email,
                hashed_password=get_password_hash(leader_pwd),
                role="team_leader",
                is_active=True
            )
            db.add(user)
            db.flush()

            # Create Team
            team = Team(
                team_code=team_code,
                team_name=team_name,
                leader_user_id=user.id,
                qualification_status="pending"
            )
            db.add(team)
            db.flush()

            # Create Team Leader Member
            leader_member = TeamMember(
                team_id=team.id,
                name=leader_name,
                email=leader_email,
                is_leader=True
            )
            db.add(leader_member)

            # Optional Member 2
            m2_name = str(row.get("member2_name", "")).strip()
            m2_email = str(row.get("member2_email", "")).strip()
            if m2_name and m2_email:
                db.add(TeamMember(team_id=team.id, name=m2_name, email=m2_email, is_leader=False))

            # Optional Member 3
            m3_name = str(row.get("member3_name", "")).strip()
            m3_email = str(row.get("member3_email", "")).strip()
            if m3_name and m3_email:
                db.add(TeamMember(team_id=team.id, name=m3_name, email=m3_email, is_leader=False))

            imported_count += 1

        except Exception as e:
            errors.append(f"Row {row_idx} error: {str(e)}")

    if imported_count > 0:
        audit = AuditLog(
            actor_user_id=admin_user_id,
            action="BULK_IMPORT_TEAMS",
            entity_type="Team",
            entity_id=None,
            details_json={"imported_count": imported_count, "error_count": len(errors)}
        )
        db.add(audit)
        db.commit()

    return imported_count, errors

def reset_team_leader_password(team_id: str, new_password: str, db: Session, admin_user_id: str) -> bool:
    """Resets the team leader password securely."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.leader:
        return False

    team.leader.hashed_password = get_password_hash(new_password)
    
    audit = AuditLog(
        actor_user_id=admin_user_id,
        action="RESET_TEAM_CREDENTIALS",
        entity_type="Team",
        entity_id=team.id,
        details_json={"team_code": team.team_code}
    )
    db.add(audit)
    db.commit()
    return True
