import json
from sqlalchemy import select
from backend.models.entities import Team, League, Match, Prediction, Follow, Pick
from backend.services.prediction import history_for


def match_json(db, m, user_id=None, detail=False):
    home, away = db.get(Team, m.home_id), db.get(Team, m.away_id)
    p = db.scalar(select(Prediction).where(Prediction.match_id == m.id))
    result = {
        k: getattr(m, k)
        for k in (
            "id",
            "league_id",
            "home_id",
            "away_id",
            "kickoff",
            "status",
            "home_goals",
            "away_goals",
            "source",
        )
    }
    result.update(
        home=home.name, away=away.name, league=db.get(League, m.league_id).name
    )
    result["prediction"] = json.loads(p.payload) if p else None
    result["prediction_id"] = p.id if p else None
    result["eligible"] = p.eligible if p else False
    result["correct"] = p.correct if p else None
    result["model_version"] = p.model_version if p else None
    result["prediction_created_at"] = p.created_at if p else None
    if user_id:
        result["following"] = db.get(Follow, (user_id, m.id)) is not None
        pick = db.scalar(
            select(Pick).where(Pick.user_id == user_id, Pick.match_id == m.id)
        )
        result["pick"] = pick.outcome if pick else None
    if detail:
        rows = [
            x
            for x in history_for(db, m)
            if {x.home_id, x.away_id} == {m.home_id, m.away_id}
        ][-5:]
        result["head_to_head"] = [
            {
                "date": x.kickoff,
                "home": db.get(Team, x.home_id).name,
                "away": db.get(Team, x.away_id).name,
                "score": f"{x.home_goals}–{x.away_goals}",
            }
            for x in reversed(rows)
        ]
    return result
