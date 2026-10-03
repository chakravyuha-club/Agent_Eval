from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.models import User, Team, TeamMember
from app.schemas.schemas import LoginRequest, TokenResponse, UserResponse
from app.core.security import verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    identifier = req.identifier.strip().lower()
    
    # Check if identifier is email or team code
    user = db.query(User).filter(User.email == identifier).first()
    team = None
    
    if not user:
        # Check team code
        team = db.query(Team).filter(Team.team_code == identifier).first()
        if team and team.leader:
            user = team.leader

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials. Check your team code / email and password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Contact the competition organizers."
        )

    if not team and user.team:
        team = user.team

    token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})
    
    return TokenResponse(
        access_token=token,
        role=user.role,
        user_id=user.id,
        email=user.email,
        team_id=team.id if team else None,
        team_code=team.team_code if team else None
    )

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    team = current_user.team
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        team_id=team.id if team else None,
        team_code=team.team_code if team else None,
        team_name=team.team_name if team else None
    )

@router.post("/logout")
def logout():
    return {"status": "success", "message": "Successfully logged out."}
