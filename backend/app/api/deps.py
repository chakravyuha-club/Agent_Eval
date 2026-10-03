from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_access_token
from app.models.models import User, Team

security = HTTPBearer()


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise _unauthorized("Could not validate credentials or token expired")
    user = db.query(User).filter(User.id == payload["sub"], User.is_active == True).first()  # noqa: E712
    # `tv` (token version) lets us revoke every outstanding token: logout / password change bump it.
    if not user or payload.get("tv", 0) != user.token_version:
        raise _unauthorized("Session is no longer valid")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Administrative privileges required for this operation")
    return current_user


def get_current_team_leader(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the caller's Team, or None for admins (callers must handle None)."""
    team = db.query(Team).filter(Team.leader_user_id == current_user.id).first()
    if not team and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only registered team leaders can access this resource")
    return team
