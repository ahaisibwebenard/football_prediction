import secrets
from fastapi import Depends, HTTPException, Request
from backend.db import get_db
from backend.models.entities import User, Session, Setting, now
from backend.utils.security import decode
from backend.config import URL


def identity(request: Request, db=Depends(get_db, scope="function")):
    claims = decode(request)
    user = db.get(User, int(claims["sub"]))
    session = db.get(Session, claims["jti"])
    if (
        not user
        or not session
        or session.user_id != user.id
        or session.revoked
        or session.expires_at <= now()
        or claims["ver"] != user.version
    ):
        raise HTTPException(401, "Session expired. Please sign in.")
    if user.suspended or (user.locked_until and user.locked_until > now()):
        raise HTTPException(403, "Account unavailable. Contact an administrator.")
    if claims.get("actor"):
        actor = db.get(User, claims["actor"])
        parent = db.get(Session, claims.get("parent"))
        if (
            not actor
            or actor.suspended
            or actor.role != "ADMIN"
            or actor.must_change
            or actor.version != claims["actor_ver"]
            or not parent
            or parent.user_id != actor.id
            or parent.revoked
            or parent.expires_at <= now()
        ):
            raise HTTPException(401, "Administrator session expired.")
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("origin") not in (None, URL):
            raise HTTPException(403, "Origin rejected.")
        if not secrets.compare_digest(
            request.headers.get("x-csrf-token", ""), session.csrf
        ):
            raise HTTPException(403, "Invalid CSRF token. Reload and try again.")
    allowed = (
        "/api/auth/me",
        "/api/auth/logout",
        "/api/auth/password",
        "/api/admin/return",
    )
    if user.must_change and request.url.path not in allowed:
        raise HTTPException(403, "Change your password before continuing.")
    setting = db.get(Setting, "maintenance")
    if (
        setting
        and setting.value == "true"
        and user.role != "ADMIN"
        and request.url.path not in allowed
    ):
        raise HTTPException(503, "PredictPro is undergoing maintenance.")
    if (now() - user.last_active).total_seconds() > 300:
        user.last_active = now()
    request.state.claims, request.state.session = claims, session
    return user


def admin(request: Request, user=Depends(identity)):
    if user.role != "ADMIN" or request.state.claims.get("actor"):
        raise HTTPException(403, "Administrator access required.")
    return user
