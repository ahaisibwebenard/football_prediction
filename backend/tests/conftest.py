import os
from pathlib import Path

os.environ["JWT_SECRET"] = "tests-use-an-isolated-signing-key-0123456789abcdef"
os.environ["DATABASE_URL"] = "sqlite:///./test_predictpro.db"
os.environ["APP_ENV"] = "development"
os.environ["APP_URL"] = "http://testserver"
os.environ["SEED_ADMIN_USERNAME"] = "admin"
os.environ["SEED_ADMIN_PASSWORD"] = "benard"
os.environ["SEED_ADMIN_EMAIL"] = "admin@predictpro.local"
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.db import engine, SessionLocal
from backend.models.entities import Base
from backend.seed.seed import main


@pytest.fixture
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    main()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def login(client, name="admin", password="benard"):
    r = client.post("/api/auth/login", json={"login": name, "password": password})
    assert r.status_code == 200, r.text
    csrf = r.json()["csrf"]
    if name == "admin" and r.json()["user"]["must_change"]:
        r = client.post(
            "/api/auth/password",
            json={"current_password": password, "password": "Admin-secure-2026!"},
            headers={"x-csrf-token": csrf},
        )
        assert r.status_code == 200, r.text
        csrf = r.json()["csrf"]
    return {"x-csrf-token": csrf}


def signup(client, name="benard"):
    r = client.post(
        "/api/auth/signup",
        json={
            "name": "Benard Test",
            "username": name,
            "email": name + "@example.com",
            "password": "Test-password-2026!",
        },
    )
    assert r.status_code == 201, r.text
    return {"x-csrf-token": r.json()["csrf"]}, r.json()["user"]
