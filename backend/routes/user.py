import json
from datetime import date as date_type, datetime, time, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, func
from backend.db import get_db
from backend.middleware.auth import identity
from backend.controllers.common import require
from backend.controllers.matches import match_json
from backend.models.entities import (
    Match,
    Team,
    League,
    Favorite,
    Follow,
    Notification,
    Prediction,
    now,
)

router = APIRouter(prefix="/api", dependencies=[Depends(identity)], tags=["Football"])


@router.get("/catalog")
def catalog(user=Depends(identity), db=Depends(get_db, scope="function")):
    return {
        "leagues": [
            {"id": x.id, "name": x.name, "code": x.code, "country": x.country}
            for x in db.scalars(select(League).order_by(League.country, League.name))
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
    query = select(Match)
    if status != "ALL":
        query = query.where(Match.status == status)
    if league:
        query = query.where(Match.league_id == league)
    if team:
        query = query.where((Match.home_id == team) | (Match.away_id == team))
    if date:
        query = query.where(func.date(Match.kickoff) == date)
    if search:
        ids = select(Team.id).where(Team.name.icontains(search, autoescape=True))
        query = query.where(Match.home_id.in_(ids) | Match.away_id.in_(ids))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.order_by(
        Match.kickoff.desc() if status == "FINISHED" else Match.kickoff
    )
    return {
        "items": [
            match_json(db, match, user.id)
            for match in db.scalars(query.limit(limit).offset(offset))
        ],
        "total": total,
    }


@router.get("/matches/{mid}")
def match(mid: int, user=Depends(identity), db=Depends(get_db, scope="function")):
    return match_json(db, require(db, Match, mid), user.id, True)


@router.get("/predictions/top")
def top_predictions(
    date: str = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    selected_date = date_type.fromisoformat(date) if date else now().date()
    day_start = datetime.combine(selected_date, time.min)
    day_end = day_start + timedelta(days=1)
    matches = list(
        db.scalars(
            select(Match)
            .join(Prediction, Prediction.match_id == Match.id)
            .where(
                Match.source == "live",
                Match.status == "SCHEDULED",
                Match.kickoff >= day_start,
                Match.kickoff < day_end,
                Match.kickoff > now(),
                Prediction.eligible.is_(True),
            )
            .order_by(Match.kickoff)
            .limit(500)
        )
    )
    ranked = []
    for fixture in matches:
        prediction = db.scalar(
            select(Prediction).where(Prediction.match_id == fixture.id)
        )
        data = json.loads(prediction.payload)
        markets = {
            "Home win": data["probabilities"]["Home"],
            "Draw": data["probabilities"]["Draw"],
            "Away win": data["probabilities"]["Away"],
            "Both teams to score · Yes": data["btts"],
            "Both teams to score · No": 1 - data["btts"],
        }
        goal_markets = {}
        for key, label in (
            ("over_1_5", "Over 1.5 goals"),
            ("under_1_5", "Under 1.5 goals"),
            ("over_2_5", "Over 2.5 goals"),
            ("under_2_5", "Under 2.5 goals"),
            ("over_3_5", "Over 3.5 goals"),
            ("under_3_5", "Under 3.5 goals"),
        ):
            if key in data.get("goal_lines", {}):
                probability = data["goal_lines"][key]
                markets[label] = probability
                goal_markets[key] = probability
        market, probability = max(markets.items(), key=lambda item: item[1])
        sample_size = sum(data["sample_sizes"][team] for team in ("home", "away"))
        ranked.append(
            (
                probability,
                sample_size,
                fixture.kickoff,
                {
                    **match_json(db, fixture, user.id),
                    "best_market": market,
                    "best_market_probability": probability,
                    "markets": {
                        "result": data["probabilities"],
                        "goals": goal_markets,
                        "both_teams_to_score": {
                            "yes": data["btts"],
                            "no": 1 - data["btts"],
                        },
                        "most_likely_score_probability": data.get(
                            "scoreline_probability"
                        ),
                    },
                },
            )
        )
    ranked.sort(key=lambda row: (-row[0], -row[1], row[2]))
    items = [row[3] for row in ranked[:10]]
    for rank, item in enumerate(items, start=1):
        item["rank"] = rank
    return {
        "date": selected_date.isoformat(),
        "items": items,
        "eligible_live_fixtures": len(ranked),
    }


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
