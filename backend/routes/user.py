import json
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, func
from backend.db import get_db
from backend.middleware.auth import identity
from backend.controllers.common import require
from backend.controllers.matches import match_json
from backend.models.entities import (
    User,
    Match,
    Team,
    League,
    Pick,
    Favorite,
    Follow,
    Notification,
    Prediction,
    now,
)
from backend.schemas import PickInput
from backend.services.prediction import outcome

router = APIRouter(prefix="/api", dependencies=[Depends(identity)], tags=["Football"])


@router.get("/catalog")
def catalog(user=Depends(identity), db=Depends(get_db, scope="function")):
    return {
        "leagues": [
            {"id": x.id, "name": x.name, "code": x.code}
            for x in db.scalars(select(League).order_by(League.name))
        ],
        "teams": [
            {
                "id": x.id,
                "name": x.name,
                "league_id": x.league_id,
                "favorite": db.get(Favorite, (user.id, x.id)) is not None,
            }
            for x in db.scalars(select(Team).order_by(Team.name))
        ],
    }


@router.get("/matches")
def matches(
    league: int | None = None,
    date: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    team: int | None = None,
    search: str = Query("", max_length=100),
    status: str = Query("SCHEDULED", pattern="^(SCHEDULED|FINISHED|ALL)$"),
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    q = select(Match)
    if status != "ALL":
        q = q.where(Match.status == status)
    if league:
        q = q.where(Match.league_id == league)
    if team:
        q = q.where((Match.home_id == team) | (Match.away_id == team))
    if date:
        q = q.where(func.date(Match.kickoff) == date)
    if search:
        ids = select(Team.id).where(Team.name.icontains(search, autoescape=True))
        q = q.where(Match.home_id.in_(ids) | Match.away_id.in_(ids))
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    q = q.order_by(Match.kickoff.desc() if status == "FINISHED" else Match.kickoff)
    return {
        "items": [
            match_json(db, m, user.id)
            for m in db.scalars(q.limit(limit).offset(offset))
        ],
        "total": total,
    }


@router.get("/matches/{mid}")
def match(mid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    return match_json(db, require(db, Match, mid), user.id, True)


@router.post("/matches/{mid}/pick")
def pick(
    mid: int,
    body: PickInput,
    request: Request,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    if request.state.claims.get("actor"):
        raise HTTPException(403, "Picks are disabled while impersonating.")
    m = require(db, Match, mid)
    # Acquire a write lock before checking the deadline and existing pick.
    from sqlalchemy import update

    db.execute(update(Match).where(Match.id == mid).values(status=Match.status))
    db.refresh(m)
    if m.status != "SCHEDULED" or m.kickoff <= now():
        raise HTTPException(409, "Picks close at kickoff.")
    p = db.scalar(select(Pick).where(Pick.user_id == user.id, Pick.match_id == mid))
    if p:
        p.outcome = body.outcome
    else:
        db.add(Pick(user_id=user.id, match_id=mid, outcome=body.outcome))
    return {"message": "Pick saved. You can change it until kickoff."}


@router.post("/matches/{mid}/follow")
def follow(mid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    m = require(db, Match, mid)
    old = db.get(Follow, (user.id, mid))
    if old:
        db.delete(old)
    else:
        if m.status != "SCHEDULED" or m.kickoff <= now():
            raise HTTPException(409, "Follow upcoming matches before kickoff.")
        db.add(Follow(user_id=user.id, match_id=mid))
    return {
        "message": "Match unfollowed."
        if old
        else "Following: a notification will appear when a result is recorded."
    }


@router.post("/favorites/{tid}")
def favorite(tid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    require(db, Team, tid)
    old = db.get(Favorite, (user.id, tid))
    if old:
        db.delete(old)
    else:
        db.add(Favorite(user_id=user.id, team_id=tid))
    return {"message": "Favorite removed." if old else "Favorite added."}


@router.get("/history")
def history(
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
    offset: int = Query(0, ge=0),
):
    rows = list(
        db.scalars(
            select(Match)
            .join(Prediction)
            .order_by(Prediction.created_at.desc())
            .limit(50)
            .offset(offset)
        )
    )
    return {"items": [match_json(db, m, user.id) for m in rows], "offset": offset}


@router.get("/leaderboard")
def leaderboard(db=Depends(get_db, scope="function")):
    results = []
    for u in db.scalars(select(User).where(User.suspended == False)):
        pairs = db.execute(
            select(Pick, Match)
            .join(Match, Match.id == Pick.match_id)
            .where(
                Pick.user_id == u.id,
                Match.status == "FINISHED",
                Pick.created_at < Match.kickoff,
            )
        ).all()
        if not pairs:
            continue
        hits = sum(p.outcome == outcome(m.home_goals, m.away_goals) for p, m in pairs)
        results.append(
            {
                "name": u.username,
                "correct": hits,
                "total": len(pairs),
                "points": hits * 3,
                "accuracy": hits / len(pairs),
                "kind": "user",
            }
        )
    for source in ("live", "sample", "manual"):
        pairs = db.execute(
            select(Prediction, Match)
            .join(Match, Match.id == Prediction.match_id)
            .where(
                Prediction.correct.is_not(None),
                Prediction.eligible == True,
                Match.source == source,
            )
        ).all()
        if pairs:
            hits = sum(p.correct for p, m in pairs)
            results.append(
                {
                    "name": f"PredictPro AI · {source}",
                    "correct": hits,
                    "total": len(pairs),
                    "points": hits * 3,
                    "accuracy": hits / len(pairs),
                    "kind": "AI",
                }
            )
    return sorted(results, key=lambda x: (-x["points"], -x["accuracy"], x["name"]))


@router.get("/notifications")
def notifications(user=Depends(identity), db=Depends(get_db, scope="function")):
    return [
        {
            "id": n.id,
            "text": n.text,
            "read": n.read,
            "created_at": n.created_at,
            "match_id": n.match_id,
        }
        for n in db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/notifications/{nid}/read")
def read(nid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    n = require(db, Notification, nid)
    if n.user_id != user.id:
        raise HTTPException(404, "Notification not found.")
    n.read = True
    return {"message": "Notification marked as read."}


@router.get("/metrics")
def metrics(db=Depends(get_db, scope="function")):
    return model_metrics(db)


def model_metrics(db):
    groups = {}
    trend = []
    pairs = db.execute(
        select(Prediction, Match)
        .join(Match, Match.id == Prediction.match_id)
        .where(Prediction.correct.is_not(None))
        .order_by(Match.kickoff)
    ).all()
    for p, m in pairs:
        key = m.source if p.eligible else m.source + " backtest"
        group = groups.setdefault(key, {"total": 0, "correct": 0, "brier_sum": 0.0})
        group["total"] += 1
        group["correct"] += int(p.correct)
        group["brier_sum"] += p.brier or 0
        if p.eligible:
            trend.append(
                {
                    "date": m.kickoff.date().isoformat(),
                    "source": m.source,
                    "correct": int(p.correct),
                    "brier": p.brier,
                }
            )
    for g in groups.values():
        g.update(
            accuracy=g["correct"] / g["total"], brier=g.pop("brier_sum") / g["total"]
        )
    return {
        "groups": groups,
        "trend": trend,
        "note": "Only predictions frozen before kickoff enter prospective accuracy. Historical backtests are separate. Brier score: lower is better (0–2).",
    }
