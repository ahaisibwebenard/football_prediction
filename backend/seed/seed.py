"""Idempotent seed: exactly one initial admin; deterministic synthetic seasons."""

import json
import os
import random
import math
from pathlib import Path
from datetime import timedelta
from sqlalchemy import delete, or_, select
from backend.db import SessionLocal
from backend.models.entities import (
    User,
    League,
    Team,
    Match,
    Setting,
    Favorite,
    Follow,
    Notification,
    Pick,
    Prediction,
    now,
)
from backend.utils.security import hash_password
from backend.services.prediction import get_prediction, evaluate


def poisson(rng, lam):
    value = 0
    p = 1.0
    limit = math.exp(-lam)
    while p > limit:
        value += 1
        p *= rng.random()
    return value - 1


def seed_sample(db):
    data = json.loads(
        Path(__file__).with_name("sample.json").read_text(encoding="utf-8")
    )
    rng = random.Random(data["seed"])
    added = 0
    for info in data["leagues"]:
        if db.scalar(select(League).where(League.code == info["code"])):
            continue
        league = League(name=info["name"], code=info["code"])
        db.add(league)
        db.flush()
        teams = [Team(name=n, league_id=league.id) for n in info["teams"]]
        db.add_all(teams)
        db.flush()
        base = now().replace(hour=15, minute=0, second=0, microsecond=0)
        # Ten rounds with all directed pairs. No future result is used to predict a prior game.
        idx = 0
        for round_no in range(3):
            for hi, h in enumerate(teams):
                for ai, a in enumerate(teams):
                    if hi == ai:
                        continue
                    idx += 1
                    m = Match(
                        league_id=league.id,
                        home_id=h.id,
                        away_id=a.id,
                        kickoff=base - timedelta(days=190 - idx * 2),
                        status="FINISHED",
                        home_goals=poisson(rng, 1.8 - hi * 0.12),
                        away_goals=poisson(rng, 1.35 - ai * 0.09),
                        source="sample",
                    )
                    db.add(m)
                    db.flush()
                    p = get_prediction(db, m, retrospective=True)
                    # Backtest rows are explicitly ineligible for live accuracy.
                    evaluate(db, m)
                    added += 1
        for i in range(6):
            h, a = teams[i], teams[(i + 1) % len(teams)]
            m = Match(
                league_id=league.id,
                home_id=h.id,
                away_id=a.id,
                kickoff=base + timedelta(days=i + 1),
                source="sample",
                status="SCHEDULED",
            )
            db.add(m)
            db.flush()
            get_prediction(db, m)
            added += 1
    return added


def clear_sample_data(db):
    data = json.loads(
        Path(__file__).with_name("sample.json").read_text(encoding="utf-8")
    )
    sample_matches = list(
        db.scalars(select(Match).where(Match.source == "sample"))
    )
    match_ids = [match.id for match in sample_matches]
    for model in (Notification, Follow, Pick, Prediction):
        if match_ids:
            db.execute(delete(model).where(model.match_id.in_(match_ids)))
    if match_ids:
        db.execute(delete(Match).where(Match.id.in_(match_ids)))

    codes = [league["code"] for league in data["leagues"]]
    for league in db.scalars(select(League).where(League.code.in_(codes))):
        teams = list(db.scalars(select(Team).where(Team.league_id == league.id)))
        for team in teams:
            used = db.scalar(
                select(Match.id)
                .where(or_(Match.home_id == team.id, Match.away_id == team.id))
                .limit(1)
            )
            if not used:
                db.execute(delete(Favorite).where(Favorite.team_id == team.id))
                db.delete(team)
        if not db.scalar(
            select(Team.id).where(Team.league_id == league.id).limit(1)
        ):
            db.delete(league)
    return len(match_ids)


def main():
    with SessionLocal() as db:
        removed = clear_sample_data(db)
        if not db.scalar(select(User).where(User.role == "ADMIN")):
            username = os.getenv("SEED_ADMIN_USERNAME")
            password = os.getenv("SEED_ADMIN_PASSWORD")
            if not username or not password:
                raise RuntimeError(
                    "Set SEED_ADMIN_USERNAME and SEED_ADMIN_PASSWORD in .env."
                )
            db.add(
                User(
                    name="PredictPro Administrator",
                    email=os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").lower(),
                    username=username.lower(),
                    password_hash=hash_password(password),
                    role="ADMIN",
                    must_change=True,
                )
            )
        if not db.get(Setting, "site_name"):
            db.add(Setting(key="site_name", value="PredictPro"))
        if not db.get(Setting, "maintenance"):
            db.add(Setting(key="maintenance", value="false"))
        db.commit()
        print(f"Initialization complete; removed {removed} synthetic matches.")


if __name__ == "__main__":
    main()
