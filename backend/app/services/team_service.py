import csv
import io
import secrets
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.models import User, Team, TeamMember, AuditLog
from app.core.security import get_password_hash

def bulk_import_teams_from_csv(csv_content: str, db: Session, admin_user_id: str, credentials_out: Optional[List[Dict[str, str]]] = None) -> Tuple[int, List[str]]:
    """
    Imports teams from a CSV file.
    Expected CSV columns: team_code,team_name,leader_name,leader_email,leader_password,member2_name,member2_email,member3_name,member3_email
    """
    reader = csv.DictReader(io.StringIO(csv_content))
    imported_count = 0
    errors = []

    for row_idx, row in enumerate(reader, start=2):
        try:
            team_code = str(row.get("team_code", "")).strip().lower()
            team_name = str(row.get("team_name", "")).strip()
            leader_email = str(row.get("leader_email", "")).strip().lower()
            leader_name = str(row.get("leader_name", "")).strip() or f"{team_name} Leader"
            leader_pwd = str(row.get("leader_password", "")).strip()
            generated = not leader_pwd
            if generated:
                leader_pwd = secrets.token_urlsafe(12) + "aA1"  # never a predictable default

            if not team_code or not team_name or not leader_email:
                errors.append(f"Row {row_idx}: Missing required fields (team_code, team_name, or leader_email).")
                continue

            # Check if team or user already exists
            existing_team = db.query(Team).filter(Team.team_code == team_code).first()
            if existing_team:
                errors.append(f"Row {row_idx}: Team code '{team_code}' already exists.")
                continue

            existing_user = db.query(User).filter(User.email == leader_email).first()
            if existing_user:
                errors.append(f"Row {row_idx}: User email '{leader_email}' already registered.")
                continue

            # Create Leader User
            leader_user = User(
                email=leader_email,
                hashed_password=get_password_hash(leader_pwd),
                role="team_leader",
                is_active=True
            )
            db.add(leader_user)
            db.flush()

            # Create Team
            team = Team(
                team_code=team_code,
                team_name=team_name,
                leader_user_id=leader_user.id,
                qualification_status="registered"
            )
            db.add(team)
            db.flush()

            # Create Leader Member
            db.add(TeamMember(
                team_id=team.id,
                name=leader_name,
                email=leader_email,
                is_leader=True
            ))

            # Add optional secondary members
            m2_name = str(row.get("member2_name", "")).strip()
            m2_email = str(row.get("member2_email", "")).strip().lower()
            if m2_name and m2_email:
                db.add(TeamMember(team_id=team.id, name=m2_name, email=m2_email, is_leader=False))

            m3_name = str(row.get("member3_name", "")).strip()
            m3_email = str(row.get("member3_email", "")).strip().lower()
            if m3_name and m3_email:
                db.add(TeamMember(team_id=team.id, name=m3_name, email=m3_email, is_leader=False))

            if generated and credentials_out is not None:
                credentials_out.append({"team_code": team_code, "email": leader_email, "password": leader_pwd})
            imported_count += 1

        except Exception as e:
            errors.append(f"Row {row_idx}: Error - {str(e)}")

    if imported_count > 0:
        db.add(AuditLog(
            actor_user_id=admin_user_id,
            action="BULK_IMPORT_TEAMS",
            entity_type="Team",
            details_json={"imported_count": imported_count, "error_count": len(errors)}
        ))
        db.commit()

    return imported_count, errors

def reset_team_leader_password(team_id: str, new_password: str, db: Session, admin_user_id: str) -> bool:
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team or not team.leader:
        return False

    team.leader.hashed_password = get_password_hash(new_password)
    team.leader.token_version += 1
    db.add(AuditLog(
        actor_user_id=admin_user_id,
        action="RESET_PASSWORD",
        entity_type="User",
        entity_id=team.leader.id,
        details_json={"team_id": team.id, "team_code": team.team_code}
    ))
    db.commit()
    return True
