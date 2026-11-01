import json
import os
from datetime import datetime
from sqlalchemy import select
import httpx
from backend.models.entities import League, Team, Match, Follow, Notification, now
from backend.services.prediction import get_prediction, evaluate


def notify_result(db, m):
    if m.status != "FINISHED":
        return
    evaluate(db, m)
    home, away = db.get(Team, m.home_id), db.get(Team, m.away_id)
    for follow in db.scalars(select(Follow).where(Follow.match_id == m.id)):
        if not db.scalar(
            select(Notification).where(
                Notification.user_id == follow.user_id, Notification.match_id == m.id
            )
        ):
            db.add(
                Notification(
                    user_id=follow.user_id,
                    match_id=m.id,
                    text=f"{home.name} {m.home_goals}–{m.away_goals} {away.name}: full time.",
                )
            )


def fetch_competition(code, key):
    with httpx.Client(timeout=20) as client:
        response = client.get(
            f"https://api.football-data.org/v4/competitions/{code}/matches",
            headers={"X-Auth-Token": key},
        )
        response.raise_for_status()
        return response.json()


def refresh(db):
    from backend.models.entities import Setting

    saved = db.get(Setting, "api_key")
    key = saved.value if saved else os.getenv("FOOTBALL_API_KEY", "")
    if not key:
        return {
            "source": "unavailable",
            "synced": 0,
            "errors": [],
            "message": "No football-data.org API key is configured. Add one in Admin settings or set FOOTBALL_API_KEY; no demo fixtures are generated.",
        }
    count = 0
    errors = []
    for code in os.getenv("FOOTBALL_COMPETITIONS", "PL,PD").split(","):
        code = code.strip()
        if not code or not code.isalnum():
            continue
        try:
            data = fetch_competition(code, key)
            league = db.scalar(select(League).where(League.code == code))
            if not league:
                league = League(
                    code=code, name=data.get("competition", {}).get("name", code)
                )
                db.add(league)
                db.flush()
            for row in sorted(data.get("matches", []), key=lambda r: r["utcDate"]):
                if not row.get("homeTeam", {}).get("id") or not row.get(
                    "awayTeam", {}
                ).get("id"):
                    continue
                teams = []
                for field in ("homeTeam", "awayTeam"):
                    item = row[field]
                    team = db.scalar(select(Team).where(Team.external_id == item["id"]))
                    if not team:
                        team = Team(
                            name=item["name"],
                            league_id=league.id,
                            external_id=item["id"],
                        )
                        db.add(team)
                        db.flush()
                    teams.append(team)
                kick = datetime.fromisoformat(
                    row["utcDate"].replace("Z", "+00:00")
                ).replace(tzinfo=None)
                status = row["status"]
                score = row.get("score", {}).get("fullTime", {})
                if status in ("SCHEDULED", "TIMED"):
                    status = "SCHEDULED"
                elif status == "FINISHED":
                    if score.get("home") is None or score.get("away") is None:
                        continue
                elif status == "POSTPONED":
                    status = "POSTPONED"
                elif status == "CANCELLED":
                    status = "CANCELLED"
                else:
                    continue  # Do not mislabel in-play, suspended or unknown states.
                m = db.scalar(select(Match).where(Match.external_id == row["id"]))
                if not m:
                    m = Match(
                        external_id=row["id"],
                        league_id=league.id,
                        home_id=teams[0].id,
                        away_id=teams[1].id,
                        kickoff=kick,
                        source="live",
                    )
                    db.add(m)
                m.status = status
                m.kickoff = kick
                m.home_goals = score.get("home") if status == "FINISHED" else None
                m.away_goals = score.get("away") if status == "FINISHED" else None
                db.flush()
                notify_result(db, m)
                count += 1
            db.commit()
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            db.rollback()
            errors.append(
                f"{code}: {type(exc).__name__}; check API plan, key and connectivity."
            )
    for m in db.scalars(
        select(Match).where(Match.status == "SCHEDULED", Match.kickoff > now())
    ):
        get_prediction(db, m)
    return {
        "source": "live" if count or not errors else "unavailable",
        "synced": count,
        "errors": errors,
        "message": "Live sync complete."
        if count
        else "No live matches returned by the provider."
        if not errors
        else "Live sync failed. Existing records were retained; no demo fixtures were created.",
    }
