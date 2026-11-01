import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response, HTTPException
from sqlalchemy import select, update, or_
from backend.db import get_db
from backend.middleware.auth import identity
from backend.models.entities import User, Reset, Session, now
from backend.schemas import Signup, Login, Password, Forgot, ResetInput, Profile
from backend.utils.security import (
    hash_password,
    verify,
    password_check,
    issue,
    public_user,
    rate,
    digest,
    revoke_all,
)
from backend.services.recovery import create_reset, send_reset
from backend.config import COOKIE, URL

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


def public_guard(request, db, action, limit):
    if request.headers.get("origin") not in (None, URL):
        raise HTTPException(403, "Origin rejected.")
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        raise HTTPException(415, "JSON required.")
    rate(
        db, action + ":" + (request.client.host if request.client else "unknown"), limit
    )


@router.post("/signup", status_code=201)
def signup(
    body: Signup,
    request: Request,
    response: Response,
    db=Depends(get_db, scope="function"),
):
    public_guard(request, db, "signup", 10)
    password_check(body.password)
    if db.scalar(
        select(User).where(
            or_(User.email == body.email, User.username == body.username)
        )
    ):
        raise HTTPException(409, "Email or username is already registered.")
    user = User(
        **body.model_dump(exclude={"password"}),
        password_hash=hash_password(body.password),
        role="USER",
    )
    db.add(user)
    db.flush()
    csrf = issue(db, user, response)
    return {"user": public_user(user), "csrf": csrf}


@router.post("/login")
def login(
    body: Login,
    request: Request,
    response: Response,
    db=Depends(get_db, scope="function"),
):
    public_guard(request, db, "login", 20)
    key = body.login.lower().strip()
    user = db.scalar(select(User).where(or_(User.email == key, User.username == key)))
    # A fixed bcrypt workload for unknown accounts reduces timing differences.
    dummy = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6Ttx2M3kyE/JDFrjKkL9lHfYzvF5K"
    good = verify(body.password, user.password_hash if user else dummy)
    if not user or not good:
        if user:
            user.failed += 1
            if user.failed >= 5:
                user.locked_until = now() + timedelta(minutes=15)
            db.commit()
        raise HTTPException(401, "Invalid login details or account unavailable.")
    if user.suspended or (user.locked_until and user.locked_until > now()):
        raise HTTPException(
            403, "Account unavailable. Contact an administrator or try later."
        )
    user.failed = 0
    user.locked_until = None
    user.last_active = now()
    csrf = issue(db, user, response)
    return {"user": public_user(user), "csrf": csrf}


@router.get("/me")
def me(request: Request, user=Depends(identity)):
    return {
        "user": public_user(user),
        "csrf": request.state.session.csrf,
        "impersonating": bool(request.state.claims.get("actor")),
    }


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    request.state.session.revoked = True
    if request.state.claims.get("parent"):
        parent = db.get(Session, request.state.claims["parent"])
        if parent:
            parent.revoked = True
    response.delete_cookie(COOKIE, path="/")
    return {"message": "Signed out."}


@router.put("/profile")
def profile(body: Profile, user=Depends(identity)):
    for key, value in body.model_dump().items():
        setattr(user, key, value)
    return {"user": public_user(user), "message": "Profile updated."}


@router.post("/password")
def password(
    body: Password,
    request: Request,
    response: Response,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    if request.state.claims.get("actor"):
        raise HTTPException(403, "Password changes are disabled while impersonating.")
    if not verify(body.current_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect.")
    password_check(body.password)
    if verify(body.password, user.password_hash):
        raise HTTPException(422, "Choose a different password.")
    user.password_hash = hash_password(body.password)
    user.must_change = False
    revoke_all(db, user)
    db.execute(update(Reset).where(Reset.user_id == user.id).values(used=True))
    csrf = issue(db, user, response)
    return {
        "message": "Password changed. Other sessions were revoked.",
        "csrf": csrf,
        "user": public_user(user),
    }


@router.post("/forgot")
def forgot(body: Forgot, request: Request, db=Depends(get_db, scope="function")):
    public_guard(request, db, "forgot", 5)
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    if user and not user.suspended:
        link = create_reset(db, user)
        db.commit()
        try:
            send_reset(user.email, link)
        except Exception:
            logging.getLogger("predictpro").error(
                "Password reset delivery failed; check SMTP configuration."
            )
    return {
        "message": "If that account can recover, a reset email has been sent. Local development writes email to backend/outbox."
    }


@router.post("/reset")
def reset(body: ResetInput, request: Request, db=Depends(get_db, scope="function")):
    public_guard(request, db, "reset", 10)
    password_check(body.password)
    # Atomic token consumption prevents concurrent reuse.
    uid = db.execute(
        update(Reset)
        .where(
            Reset.digest == digest(body.token),
            Reset.used == False,
            Reset.expires_at > now(),
        )
        .values(used=True)
        .returning(Reset.user_id)
    ).scalar_one_or_none()
    if not uid:
        raise HTTPException(400, "Reset link is invalid or expired.")
    user = db.get(User, uid)
    if user.suspended:
        raise HTTPException(403, "Ask an administrator to activate your account.")
    user.password_hash = hash_password(body.password)
    user.must_change = False
    user.failed = 0
    user.locked_until = None
    revoke_all(db, user)
    return {"message": "Password reset. Sign in with your new password."}
