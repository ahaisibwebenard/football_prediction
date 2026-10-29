from datetime import timedelta
from sqlalchemy import select
from conftest import login, signup
from backend.models.entities import User, Audit, Reset, now
from backend.utils.security import hash_password, verify


def test_admin_hash_and_forced_change(client, db):
    u = db.scalar(select(User).where(User.username == "admin"))
    assert u.password_hash != "benard" and verify("benard", u.password_hash)
    r = client.post("/api/auth/login", json={"login": "admin", "password": "benard"})
    assert (
        "HttpOnly" in r.headers["set-cookie"]
        and "SameSite=strict" in r.headers["set-cookie"]
    )
    assert client.get("/api/admin/overview").status_code == 403
    login(client)
    assert client.get("/api/admin/overview").status_code == 200


def test_auth_role_and_csrf(client):
    assert client.get("/api/matches").status_code == 401
    headers, u = signup(client)
    assert client.get("/api/admin/users").status_code == 403
    assert (
        client.put(
            "/api/auth/profile",
            json={"name": "X X", "email": "x@example.com", "username": "xxx"},
        ).status_code
        == 403
    )
    assert (
        client.put(
            "/api/auth/profile",
            json={"name": "X X", "email": "x@example.com", "username": "xxx"},
            headers={**headers, "origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout", json={}, headers=headers).status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_input_and_sql_injection(client):
    h, u = signup(client)
    assert client.get("/api/matches?search=%27%20OR%201%3D1%20--").status_code == 200
    bad = client.put(
        "/api/auth/profile",
        json={
            "name": "<script>alert(1)</script>",
            "email": "x@example.com",
            "username": "xxx",
        },
        headers=h,
    )
    assert bad.status_code == 422
    assert client.get("/api/matches?limit=999999").status_code == 422


def test_lock_and_rate_limit(client):
    signup(client)
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/login", json={"login": "benard", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login",
            json={"login": "benard", "password": "Test-password-2026!"},
        ).status_code
        == 403
    )
    for _ in range(21):
        r = client.post("/api/auth/login", json={"login": "unknown", "password": "bad"})
    assert r.status_code == 429


def test_recovery_is_one_time_and_revokes_sessions(client, monkeypatch):
    h, u = signup(client)
    links = []
    monkeypatch.setattr(
        "backend.routes.auth.send_reset", lambda email, link: links.append(link)
    )
    assert (
        client.post(
            "/api/auth/forgot", json={"email": "benard@example.com"}
        ).status_code
        == 200
    )
    token = links[0].split("token=")[1]
    r = client.post(
        "/api/auth/reset", json={"token": token, "password": "New-password-2026!"}
    )
    assert r.status_code == 200
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/reset", json={"token": token, "password": "New-password-2026!"}
        ).status_code
        == 400
    )


def test_admin_recovery_suspend_unlock_and_audit(client, db):
    h, u = signup(client)
    admin = login(client)
    assert (
        client.post(
            f"/api/admin/users/{u['id']}/state", json={"suspended": True}, headers=admin
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/api/auth/login",
            json={"login": "benard", "password": "Test-password-2026!"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/admin/users/{u['id']}/state",
            json={"suspended": False},
            headers=admin,
        ).status_code
        == 200
    )
    r = client.post(
        f"/api/admin/users/{u['id']}/temporary-password", json={}, headers=admin
    )
    temp = r.json()["temporary_password"]
    assert len(temp) >= 15
    logs = client.get("/api/admin/audit").json()
    assert any(x["action"] == "TEMPORARY_PASSWORD" and x["ip"] for x in logs)
    assert temp not in str(logs)
    r = client.post("/api/auth/login", json={"login": "benard", "password": temp})
    assert r.json()["user"]["must_change"] is True
    assert client.get("/api/matches").status_code == 403


def test_impersonation_boundary_and_return(client):
    h, u = signup(client)
    admin = login(client)
    r = client.post(f"/api/admin/users/{u['id']}/impersonate", json={}, headers=admin)
    assert r.status_code == 200, r.text
    h = {"x-csrf-token": r.json()["csrf"]}
    assert client.get("/api/auth/me").json()["impersonating"] is True
    assert client.get("/api/admin/users").status_code == 403
    assert (
        client.post(
            "/api/auth/password",
            json={
                "current_password": "Test-password-2026!",
                "password": "Should-not-work!",
            },
            headers=h,
        ).status_code
        == 403
    )
    r = client.post("/api/admin/return", json={}, headers=h)
    assert r.status_code == 200 and r.json()["user"]["role"] == "ADMIN"
    actions = [x["action"] for x in client.get("/api/admin/audit").json()]
    assert "IMPERSONATE_START" in actions and "IMPERSONATE_END" in actions


def test_cannot_delete_self_or_final_admin(client):
    h = login(client)
    u = client.get("/api/auth/me").json()["user"]
    assert (
        client.delete("/api/admin/users/" + str(u["id"]), headers=h).status_code == 409
    )


def test_expired_reset(client, db):
    from backend.services.recovery import create_reset

    h, u = signup(client)
    obj = db.get(User, u["id"])
    url = create_reset(db, obj)
    db.flush()
    reset = db.scalar(select(Reset).where(Reset.user_id == u["id"]))
    reset.expires_at = now() - timedelta(seconds=1)
    db.commit()
    assert (
        client.post(
            "/api/auth/reset",
            json={"token": url.split("token=")[1], "password": "New-password-2026!"},
        ).status_code
        == 400
    )


def test_user_management_profile_favorites_and_reset_link(client):
    h = login(client)
    payload = {
        "name": "Test Person",
        "email": "person@example.com",
        "username": "person",
        "password": "Initial-password-2026!",
        "role": "USER",
    }
    r = client.post("/api/admin/users", json=payload, headers=h)
    assert r.status_code == 201, r.text
    uid = r.json()["user"]["id"]
    assert len(client.get("/api/admin/users?q=person").json()) == 1
    assert client.get(f"/api/admin/users/{uid}").json()["username"] == "person"
    profile = {
        "name": "Changed Person",
        "email": "person@example.com",
        "username": "person",
        "role": "USER",
    }
    assert (
        client.put(f"/api/admin/users/{uid}", json=profile, headers=h).status_code
        == 200
    )
    link = client.post(f"/api/admin/users/{uid}/reset", json={}, headers=h).json()[
        "reset_link"
    ]
    assert (
        client.post(
            "/api/auth/reset",
            json={"token": link.split("token=")[1], "password": "Reset-password-2026!"},
        ).status_code
        == 200
    )
    r = client.post(
        "/api/auth/login", json={"login": "person", "password": "Reset-password-2026!"}
    )
    ph = {"x-csrf-token": r.json()["csrf"]}
    assert (
        client.put(
            "/api/auth/profile",
            json={k: v for k, v in profile.items() if k != "role"},
            headers=ph,
        ).status_code
        == 200
    )
    tid = client.get("/api/catalog").json()["teams"][0]["id"]
    assert (
        client.post("/api/favorites/" + str(tid), json={}, headers=ph).status_code
        == 200
    )
    assert (
        next(t for t in client.get("/api/catalog").json()["teams"] if t["id"] == tid)[
            "favorite"
        ]
        is True
    )
    assert client.get("/api/history").status_code == 200
    assert client.get("/api/leaderboard").status_code == 200
    h = login(client, password="Admin-secure-2026!")
    assert client.delete("/api/admin/users/" + str(uid), headers=h).status_code == 200
    assert client.get("/api/admin/users/" + str(uid)).status_code == 404


def test_static_assets_security_headers_and_validation_redaction(client):
    index = client.get("/")
    assert index.status_code == 200 and "PredictPro" in index.text
    assert "script-src 'self'" in index.headers["content-security-policy"]
    assert index.headers["x-frame-options"] == "DENY"
    assert client.get("/assets/vendor/chart.umd.js").status_code == 200
    assert client.get("/assets/app.js").status_code == 200
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/openapi.json").status_code == 200
    result = client.post(
        "/api/auth/signup",
        json={
            "name": "A",
            "email": "bad",
            "username": "x",
            "password": "private-value",
        },
    )
    assert result.status_code == 422 and "private-value" not in result.text
