import hashlib
import secrets
from datetime import timedelta
import bcrypt
import jwt
from fastapi import HTTPException, Request, Response
from sqlalchemy import select, update
from backend.config import SECRET, COOKIE, SECURE
from backend.models.entities import Session, User, RateBucket, now


def hash_password(value):
    return bcrypt.hashpw(value.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify(value, hashed):
    return len(value.encode()) <= 72 and bcrypt.checkpw(value.encode(), hashed.encode())


def password_check(value):
    if len(value) < 10 or len(value.encode()) > 72:
        raise HTTPException(
            422, "Password must have at least 10 characters and at most 72 UTF-8 bytes."
        )
    return value


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def rate(db, key, limit=10, seconds=900):
    # SQLite serializes writers; the atomic increment is shared by all workers.
    from sqlalchemy.dialects.sqlite import insert

    db.execute(
        insert(RateBucket)
        .values(key=key, count=0, started=now())
        .on_conflict_do_nothing()
    )
    db.execute(
        update(RateBucket)
        .where(
            RateBucket.key == key,
            RateBucket.started < now() - timedelta(seconds=seconds),
        )
        .values(count=0, started=now())
    )
    count = db.execute(
        update(RateBucket)
        .where(RateBucket.key == key)
        .values(count=RateBucket.count + 1)
        .returning(RateBucket.count)
    ).scalar_one()
    db.commit()
    if count > limit:
        raise HTTPException(
            429,
            "Too many attempts. Try again later.",
            headers={"Retry-After": str(seconds)},
        )


def issue(db, user, response: Response, actor=None, parent=None):
    sid, csrf = secrets.token_hex(24), secrets.token_hex(24)
    expiry = now() + timedelta(hours=8)
    session = Session(id=sid, user_id=user.id, csrf=csrf, expires_at=expiry)
    db.add(session)
    claims = {
        "sub": str(user.id),
        "ver": user.version,
        "jti": sid,
        "exp": expiry,
        "iat": now(),
    }
    if actor:
        claims.update(actor=actor.id, actor_ver=actor.version, parent=parent)
    token = jwt.encode(claims, SECRET, algorithm="HS256")
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=SECURE,
        samesite="strict",
        max_age=28800,
        path="/",
    )
    return csrf


def decode(request: Request):
    try:
        return jwt.decode(
            request.cookies.get(COOKIE, ""),
            SECRET,
            algorithms=["HS256"],
            options={"require": ["sub", "ver", "jti", "exp", "iat"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Please sign in.")


def revoke_all(db, user):
    user.version += 1
    db.execute(update(Session).where(Session.user_id == user.id).values(revoked=True))


def public_user(user):
    return {
        k: getattr(user, k)
        for k in (
            "id",
            "name",
            "email",
            "username",
            "role",
            "suspended",
            "must_change",
            "created_at",
            "last_active",
            "failed",
            "locked_until",
        )
    }
