from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional
from app.core.config import settings
from app.db.session import get_db
from app.models.models import Team, Competition, LeaderboardSnapshot
from app.schemas.schemas import PublicLeaderboardResponse, LeaderboardEntry

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

def utcnow():
    return datetime.now(timezone.utc)

@router.get("/public", response_model=PublicLeaderboardResponse)
def get_public_leaderboard(
    stage: Optional[int] = Query(None, description="Stage 1 or 2"),
    db: Session = Depends(get_db)
):
    comp = db.query(Competition).first()
    current_stage = stage or (comp.current_stage if comp else 1)

    # Check for latest published official snapshot
    snapshot = db.query(LeaderboardSnapshot).filter(
        LeaderboardSnapshot.stage == current_stage,
        LeaderboardSnapshot.is_published == True
    ).order_by(LeaderboardSnapshot.created_at.desc()).first()

    if snapshot:
        entries = []
        for idx, item in enumerate(snapshot.snapshot_json, start=1):
            entries.append(LeaderboardEntry(
                rank=item.get("rank", idx),
                team_id=item.get("team_id", ""),
                team_code=item.get("team_code", ""),
                team_name=item.get("team_name", ""),
                stage1_score=item.get("stage1_score", 0.0),
                stage2_score=item.get("stage2_score"),
                final_score=item.get("final_score"),
                qualification_status=item.get("qualification_status", "registered"),
                is_provisional=False
            ))
        return PublicLeaderboardResponse(
            stage=current_stage,
            is_published=True,
            last_updated=snapshot.created_at,
            entries=entries
        )

    # Live scores are derived from private labels: only expose them if explicitly enabled (dev/demo).
    if not settings.PUBLIC_PROVISIONAL_LEADERBOARD:
        return PublicLeaderboardResponse(stage=current_stage, is_published=False, last_updated=utcnow(), entries=[])

    # Live provisional calculation
    if current_stage == 1:
        teams = db.query(Team).order_by(Team.stage1_score.desc(), Team.created_at.asc()).all()
        entries = [
            LeaderboardEntry(
                rank=idx,
                team_id=t.id,
                team_code=t.team_code,
                team_name=t.team_name,
                stage1_score=t.stage1_score,
                qualification_status=t.qualification_status,
                is_provisional=True
            ) for idx, t in enumerate(teams, start=1)
        ]
    else:
        teams = db.query(Team).filter(Team.qualification_status == "qualified").order_by(
            Team.final_score.desc(), Team.stage2_score.desc(), Team.stage1_score.desc()
        ).all()
        entries = [
            LeaderboardEntry(
                rank=idx,
                team_id=t.id,
                team_code=t.team_code,
                team_name=t.team_name,
                stage1_score=t.stage1_score,
                stage2_score=t.stage2_score,
                final_score=t.final_score,
                qualification_status=t.qualification_status,
                is_provisional=True
            ) for idx, t in enumerate(teams, start=1)
        ]

    return PublicLeaderboardResponse(
        stage=current_stage,
        is_published=False,
        last_updated=utcnow(),
        entries=entries
    )
