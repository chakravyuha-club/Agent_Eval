import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.passwords import DUMMY_HASH, validate_password_strength
from app.core.ratelimit import login_throttle
from app.core.security import create_access_token, get_password_hash, verify_and_check_rehash
from app.db.session import get_db
from app.models.models import AuditLog, Team, User
from app.schemas.schemas import LoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
log = logging.getLogger("agentscore.auth")
INVALID = "Invalid credentials. Check your team code / email and password."


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, request: Request, db: Session = Depends(get_db)):
    identifier = req.identifier.strip().lower()
    ip = request.client.host if request.client else "unknown"
    # Throttle per identifier AND per ip so neither a targeted nor a spraying attack gets unlimited guesses.
    keys = (f"id:{identifier}", f"ip:{ip}")
    for k in keys:
        allowed, retry = login_throttle.check(k)
        if not allowed:
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.",
                                headers={"Retry-After": str(retry)})

    user = db.query(User).filter(User.email == identifier).first()
    team = None
    if not user:
        team = db.query(Team).filter(Team.team_code == identifier).first()
        if team and team.leader:
            user = team.leader

    # Always do one password verification (dummy hash if no user) so timing does not reveal valid accounts.
    ok, needs_rehash = verify_and_check_rehash(req.password, user.hashed_password if user else DUMMY_HASH)
    if not user or not ok:
        for k in keys:
            login_throttle.record_failure(k)
        log.warning("failed login id=%s ip=%s", identifier, ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=INVALID)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive. Contact the competition organizers.")

    for k in keys:
        login_throttle.record_success(k)
    if needs_rehash:  # transparently upgrade legacy 100k hashes
        user.hashed_password = get_password_hash(req.password)
        db.commit()

    team = team or user.team
    token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email, "tv": user.token_version})
    return TokenResponse(access_token=token, role=user.role, user_id=user.id, email=user.email,
                         team_id=team.id if team else None, team_code=team.team_code if team else None)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    team = current_user.team
    return UserResponse(id=current_user.id, email=current_user.email, role=current_user.role,
                        is_active=current_user.is_active, created_at=current_user.created_at,
                        team_id=team.id if team else None, team_code=team.team_code if team else None,
                        team_name=team.team_name if team else None)


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Revokes ALL tokens of this user (token_version bump)."""
    current_user.token_version += 1
    db.commit()
    return {"status": "success", "message": "Successfully logged out."}


@router.post("/change-password")
def change_password(req: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ok, _ = verify_and_check_rehash(req.current_password, current_user.hashed_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    try:
        validate_password_strength(req.new_password)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    current_user.hashed_password = get_password_hash(req.new_password)
    current_user.token_version += 1  # invalidate every existing session
    db.add(AuditLog(actor_user_id=current_user.id, action="CHANGE_PASSWORD", entity_type="User", entity_id=current_user.id, details_json={}))
    db.commit()
    return {"status": "success", "message": "Password changed. Please log in again."}
