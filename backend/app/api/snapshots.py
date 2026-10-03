"""Leaderboard snapshot lifecycle: frozen (unpublished) -> approved by an admin -> published. All audited."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.models.models import AuditLog, LeaderboardSnapshot, User

router = APIRouter(prefix="/admin/snapshots", tags=["Administrator"])


def _now():
    return datetime.now(timezone.utc)


def _get(db: Session, snapshot_id: str) -> LeaderboardSnapshot:
    snap = db.query(LeaderboardSnapshot).filter(LeaderboardSnapshot.id == snapshot_id).first()
    if not snap:
        raise HTTPException(status_code=404, detail="Snapshot not found.")
    return snap


@router.get("")
def list_snapshots(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    snaps = db.query(LeaderboardSnapshot).order_by(LeaderboardSnapshot.created_at.desc()).all()
    return [{"id": s.id, "stage": s.stage, "created_at": s.created_at, "is_published": s.is_published,
             "approved_by": s.approved_by, "approved_at": s.approved_at, "entries": len(s.snapshot_json or [])} for s in snaps]


@router.get("/{snapshot_id}")
def review_snapshot(snapshot_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = _get(db, snapshot_id)
    return {"id": s.id, "stage": s.stage, "is_published": s.is_published, "approved_by": s.approved_by,
            "approved_at": s.approved_at, "entries": s.snapshot_json}


@router.post("/{snapshot_id}/approve")
def approve_snapshot(snapshot_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = _get(db, snapshot_id)
    if s.is_published:
        raise HTTPException(status_code=409, detail="Snapshot is already published.")
    if s.approved_at:
        raise HTTPException(status_code=409, detail="Snapshot is already approved.")
    s.approved_by, s.approved_at = admin.id, _now()
    db.add(AuditLog(actor_user_id=admin.id, action="APPROVE_SNAPSHOT", entity_type="LeaderboardSnapshot", entity_id=s.id,
                    details_json={"stage": s.stage, "entries": len(s.snapshot_json or [])}))
    db.commit()
    return {"status": "success", "snapshot_id": s.id, "approved": True}


@router.post("/{snapshot_id}/publish")
def publish_snapshot(snapshot_id: str, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    s = _get(db, snapshot_id)
    if s.is_published:
        raise HTTPException(status_code=409, detail="Snapshot is already published.")
    if not s.approved_at:
        raise HTTPException(status_code=409, detail="Snapshot must be approved before it can be published.")
    s.is_published, s.published_at = True, _now()
    db.add(AuditLog(actor_user_id=admin.id, action="PUBLISH_SNAPSHOT", entity_type="LeaderboardSnapshot", entity_id=s.id,
                    details_json={"stage": s.stage}))
    db.commit()
    return {"status": "success", "snapshot_id": s.id, "published": True}
