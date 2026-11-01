import json
from datetime import timedelta
from sqlalchemy import select
from conftest import login, signup
from backend.models.entities import Match, Prediction, now
from backend.services.prediction import (
    calculate,
    get_prediction,
    evaluate,
    history_for,
    retrain,
)


def test_poisson_distribution():
    p = calculate(1, 2, [])
    assert abs(sum(p["probabilities"].values()) - 1) < 1e-9
    assert abs(p["over25"] + p["under25"] - 1) < 1e-9
    assert abs(p["goal_lines"]["over_1_5"] + p["goal_lines"]["under_1_5"] - 1) < 1e-9
    assert p["goal_lines"]["over_1_5"] >= p["goal_lines"]["over_2_5"]
    assert p["goal_lines"]["over_2_5"] >= p["goal_lines"]["over_3_5"]
    assert 0 < p["scoreline_probability"] < 1
    assert 0 <= p["btts"] <= 1
    assert p["expected_goals"]["home"] > p["expected_goals"]["away"]
    assert p["confidence"] == "Low" and len(p["explanation"]) >= 5


def test_initialization_cleanup_removes_sample_fixtures(client, db):
    from backend.seed.seed import clear_sample_data

    before = db.scalar(select(Match).where(Match.source == "sample"))
    assert before is not None
    removed = clear_sample_data(db)
    db.commit()
    assert removed > 0
    assert db.scalar(select(Match).where(Match.source == "sample")) is None


def test_snapshots_no_leakage_and_metrics(client, db):
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    p = get_prediction(db, m)
    snapshot = p.payload
    assert all(x.kickoff < m.kickoff for x in history_for(db, m))
    m.status = "FINISHED"
    m.home_goals = 2
    m.away_goals = 1
    evaluate(db, m)
    db.commit()
    assert get_prediction(db, m).payload == snapshot
    assert p.correct is not None and 0 <= p.brier <= 2
    h, u = signup(client)
    metrics = client.get("/api/metrics").json()
    assert "sample backtest" in metrics["groups"]
    assert "live" not in metrics["groups"]


def test_history_cannot_read_future_results(client, db):
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    original = calculate(m.home_id, m.away_id, history_for(db, m))
    future = Match(
        league_id=m.league_id,
        home_id=m.home_id,
        away_id=m.away_id,
        kickoff=m.kickoff + timedelta(days=1),
        status="FINISHED",
        home_goals=40,
        away_goals=0,
        source=m.source,
    )
    db.add(future)
    db.flush()
    assert calculate(m.home_id, m.away_id, history_for(db, m)) == original


def test_follow_and_notification_without_user_picks(client, db):
    h, u = signup(client)
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    assert (
        client.post(f"/api/matches/{m.id}/follow", json={}, headers=h).status_code
        == 200
    )
    from backend.services.football import notify_result

    m.kickoff = now() - timedelta(days=1)
    m.status = "FINISHED"
    m.home_goals = 2
    m.away_goals = 0
    notify_result(db, m)
    notify_result(db, m)
    db.commit()
    rows = client.get("/api/notifications").json()
    assert len(rows) == 1
    assert (
        client.post(
            "/api/notifications/" + str(rows[0]["id"]) + "/read", json={}, headers=h
        ).status_code
        == 200
    )


def test_offline_sync_and_calibration(client, db, monkeypatch):
    monkeypatch.delenv("FOOTBALL_API_KEY", raising=False)
    h = login(client)
    before = client.get("/api/matches?status=ALL").json()["total"]
    report = client.post("/api/admin/sync", json={}, headers=h).json()
    assert report["source"] == "unavailable"
    assert client.get("/api/matches?status=ALL").json()["total"] == before
    m = db.scalar(select(Match).where(Match.status == "SCHEDULED"))
    snapshot = get_prediction(db, m).payload
    result = client.post("/api/admin/retrain", json={}, headers=h)
    assert result.status_code == 200
    assert result.json()["message"].startswith("Need at least 21 earlier results")
    assert get_prediction(db, m).payload == snapshot


def test_catalog_crud_and_settings(client):
    h = login(client)
    r = client.post(
        "/api/admin/leagues",
        json={"name": "Uganda Test League", "code": "UG_TEST", "country": "Uganda"},
        headers=h,
    )
    assert r.status_code == 201
    lid = r.json()["id"]
    assert any(
        row["country"] == "Uganda"
        for row in client.get("/api/catalog").json()["leagues"]
        if row["id"] == lid
    )
    r = client.post(
        "/api/admin/teams",
        json={"name": "Kabale Test Team", "league_id": lid},
        headers=h,
    )
    assert r.status_code == 201
    tid = r.json()["id"]
    assert client.delete("/api/admin/leagues/" + str(lid), headers=h).status_code == 409
    assert (
        client.put(
            "/api/admin/teams/" + str(tid),
            json={"name": "Kabale Renamed", "league_id": lid},
            headers=h,
        ).status_code
        == 200
    )
    assert client.delete("/api/admin/teams/" + str(tid), headers=h).status_code == 200
    assert client.delete("/api/admin/leagues/" + str(lid), headers=h).status_code == 200
    assert (
        client.put(
            "/api/admin/settings",
            json={"site_name": "PredictPro Uganda", "maintenance": True},
            headers=h,
        ).status_code
        == 200
    )
    h, u = signup(client, "other")
    assert client.get("/api/matches").status_code == 503


def test_live_ingestion_and_filters(client, monkeypatch):
    from datetime import datetime, timezone

    h = login(client)
    monkeypatch.setenv("FOOTBALL_API_KEY", "test-api-key")
    monkeypatch.setenv("FOOTBALL_COMPETITIONS", "PL")
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    payload = {
        "competition": {"name": "Premier League", "area": {"name": "England"}},
        "matches": [
            {
                "id": 900001,
                "utcDate": future,
                "status": "TIMED",
                "homeTeam": {"id": 10001, "name": "Live Home"},
                "awayTeam": {"id": 10002, "name": "Live Away"},
                "score": {"fullTime": {"home": None, "away": None}},
            }
        ],
    }
    monkeypatch.setattr(
        "backend.services.football.fetch_competition", lambda *args, **kwargs: payload
    )
    assert client.post("/api/admin/sync", json={}, headers=h).json()["synced"] == 1
    assert client.post("/api/admin/sync", json={}, headers=h).json()["synced"] == 1
    rows = client.get("/api/matches?search=Live%20Home").json()["items"]
    assert len(rows) == 1 and rows[0]["source"] == "live" and rows[0]["eligible"]
    assert rows[0]["country"] == "England"
    hot = client.get("/api/predictions/top?date=" + future[:10]).json()
    assert len(hot["items"]) == 1
    assert hot["date"] == future[:10]
    assert hot["items"][0]["best_market_probability"] > 0
    assert hot["items"][0]["best_market"]
    markets = hot["items"][0]["markets"]
    assert abs(markets["goals"]["over_2_5"] + markets["goals"]["under_2_5"] - 1) < 1e-9
    assert abs(markets["both_teams_to_score"]["yes"] + markets["both_teams_to_score"]["no"] - 1) < 1e-9
    assert client.get("/api/predictions/top?date=2000-01-01").json()["items"] == []
    tid = rows[0]["home_id"]
    lid = rows[0]["league_id"]
    assert len(client.get(f"/api/matches?team={tid}&league={lid}").json()["items"]) == 1
    assert client.get("/api/matches?date=" + future[:10]).json()["total"] >= 1


def test_live_failure_does_not_add_sample_data(client, monkeypatch):
    import httpx

    h = login(client)
    monkeypatch.setenv("FOOTBALL_API_KEY", "unavailable-key")
    monkeypatch.setenv("FOOTBALL_COMPETITIONS", "PL")

    def unavailable(*args, **kwargs):
        raise httpx.ConnectError("unreachable")

    monkeypatch.setattr("backend.services.football.fetch_competition", unavailable)
    before = client.get("/api/matches?status=ALL").json()["total"]
    result = client.post("/api/admin/sync", json={}, headers=h)
    assert result.status_code == 200 and result.json()["source"] == "unavailable"
    assert client.get("/api/matches?status=ALL").json()["total"] == before
