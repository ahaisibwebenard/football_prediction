from fastapi import HTTPException
from backend.models.entities import Audit


def require(db, model, pk):
    obj = db.get(model, pk)
    if not obj:
        raise HTTPException(404, "Record not found.")
    return obj


def audit(db, request, actor, action, target):
    db.add(
        Audit(
            actor=f"{actor.username} (#{actor.id})",
            action=action,
            target=str(target)[:100],
            ip=request.client.host if request.client else "unknown",
        )
    )
