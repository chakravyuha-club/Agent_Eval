from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from app.db.session import get_db
from app.models.models import Team, Competition, LeaderboardSnapshot
from app.schemas.schemas import PublicLeaderboardResponse, LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

def utcnow():
    return datetime.now(timezone.utc)

@router.get("/public", response_model=PublicLeaderboardResponse)
def get_public_leaderboard(
    stage: Optional[int] = Query(None, description="Stage 1 or Stage 2 leaderboard"),
    db: Session = Depends(get_db)
):
    comp = db.query(Competition).first()
    current_stage = stage or (comp.current_stage if comp else 1)

    # Check if a frozen/published snapshot exists for the requested stage
    snapshot = db.query(LeaderboardSnapshot).filter(
        LeaderboardSnapshot.stage == current_stage,
        LeaderboardSnapshot.is_published == True
    ).order_by(LeaderboardSnapshot.created_at.desc()).first()

    if snapshot and snapshot.snapshot_json:
        raw_entries = snapshot.snapshot_json
        entries = []
        for e in raw_entries:
            entries.append(LeaderboardEntry(
                rank=e.get("rank", 0),
                team_id=e.get("team_id", ""),
                team_code=e.get("team_code", ""),
                team_name=e.get("team_name", ""),
                stage1_score=e.get("stage1_score", 0.0),
                stage2_score=e.get("stage2_score") if current_stage == 2 else None,
                final_score=e.get("final_score") if current_stage == 2 else None,
                qualification_status="qualified" if e.get("qualified") or e.get("is_winner") else "pending",
                is_provisional=False
            ))
        return PublicLeaderboardResponse(
            stage=current_stage,
            is_published=True,
            last_updated=snapshot.published_at or snapshot.created_at,
            entries=entries
        )

    # Live provisional calculation
    if current_stage == 1:
        teams = db.query(Team).order_by(Team.stage1_score.desc(), Team.created_at.asc()).all()
    else:
        teams = db.query(Team).filter(Team.qualification_status == "qualified").order_by(
            Team.final_score.desc(), Team.stage2_score.desc()
        ).all()

    entries = []
    for idx, t in enumerate(teams, 1):
        entries.append(LeaderboardEntry(
            rank=idx,
            team_id=t.id,
            team_code=t.team_code,
            team_name=t.team_name,
            stage1_score=t.stage1_score,
            stage2_score=t.stage2_score if current_stage == 2 else None,
            final_score=t.final_score if current_stage == 2 else None,
            qualification_status=t.qualification_status,
            is_provisional=True
        ))

    return PublicLeaderboardResponse(
        stage=current_stage,
        is_published=False,
        last_updated=utcnow(),
        entries=entries
    )
