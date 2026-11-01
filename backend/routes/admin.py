import json
import os
import secrets
from datetime import timedelta
from fastapi import APIRouter, Depends, Request, Response, HTTPException, Query
from sqlalchemy import select, func, update
from backend.db import get_db
from backend.middleware.auth import admin, identity
from backend.models.entities import (
    User,
    Match,
    Team,
    League,
    Prediction,
    Audit,
    Setting,
    Session,
    Reset,
    now,
)
from backend.schemas import (
    UserCreate,
    UserEdit,
    StateInput,
    LeagueInput,
    TeamInput,
    MatchInput,
    SettingsInput,
)
from backend.utils.security import (
    public_user,
    hash_password,
    password_check,
    revoke_all,
    issue,
)
from backend.controllers.common import require, audit
from backend.controllers.matches import match_json
from backend.services.recovery import create_reset
from backend.services.football import refresh, notify_result
from backend.services.prediction import get_prediction, retrain
from backend.routes.user import model_metrics

router = APIRouter(prefix="/api/admin", tags=["Administration"])


def protect_admin(db, target, actor, destructive=False):
    # Serialize last-admin checks so concurrent requests cannot remove all admins.
    db.execute(update(User).where(User.id == actor.id).values(version=User.version))
    if target.id == actor.id and destructive:
        raise HTTPException(
            409,
            "Use your profile for your own account. This action cannot target yourself.",
        )
    if target.role == "ADMIN" and not target.suspended:
        count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == "ADMIN", User.suspended == False)
        )
        if count <= 1 and destructive:
            raise HTTPException(409, "At least one active administrator is required.")


@router.get("/overview")
def overview(actor=Depends(admin), db=Depends(get_db, scope="function")):
    activity = list(
        db.scalars(select(Audit).order_by(Audit.created_at.desc()).limit(12))
    )
    daily = db.execute(
        select(func.date(Audit.created_at), func.count())
        .group_by(func.date(Audit.created_at))
        .order_by(func.date(Audit.created_at).desc())
        .limit(14)
    ).all()
    return {
        "total_users": db.scalar(select(func.count()).select_from(User)),
        "active_users": db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.last_active > now() - timedelta(days=30), User.suspended == False
            )
        ),
        "predictions": db.scalar(select(func.count()).select_from(Prediction)),
        "metrics": model_metrics(db),
        "recent": [
            {
                "actor": a.actor,
                "action": a.action,
                "target": a.target,
                "created_at": a.created_at,
            }
            for a in activity
        ],
        "daily": [{"date": d, "count": n} for d, n in reversed(daily)],
    }


@router.get("/users")
def users(
    q: str = Query("", max_length=100),
    offset: int = Query(0, ge=0),
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    rows = db.scalars(
        select(User)
        .where(
            User.username.icontains(q, autoescape=True)
            | User.email.icontains(q, autoescape=True)
            | User.name.icontains(q, autoescape=True)
        )
        .order_by(User.id)
        .offset(offset)
        .limit(50)
    )
    return [public_user(u) for u in rows]


@router.get("/users/{uid}")
def user_detail(uid: int, actor=Depends(admin), db=Depends(get_db, scope="function")):
    return public_user(require(db, User, uid))


@router.post("/users", status_code=201)
def create_user(
    body: UserCreate,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    password_check(body.password)
    user = User(
        **body.model_dump(exclude={"password"}),
        password_hash=hash_password(body.password),
        must_change=True,
    )
    db.add(user)
    db.flush()
    audit(db, request, actor, "CREATE_USER", user.id)
    return {
        "message": "User created. Password change required.",
        "user": public_user(user),
    }


@router.put("/users/{uid}")
def edit_user(
    uid: int,
    body: UserEdit,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if target.role != body.role:
        protect_admin(db, target, actor, True)
        revoke_all(db, target)
    for k, v in body.model_dump().items():
        setattr(target, k, v)
    audit(db, request, actor, "EDIT_USER", uid)
    return {"message": "User updated."}


@router.post("/users/{uid}/state")
def state(
    uid: int,
    body: StateInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    protect_admin(db, target, actor, body.suspended)
    target.suspended = body.suspended
    target.failed = 0
    target.locked_until = None
    revoke_all(db, target)
    audit(
        db, request, actor, "SUSPEND_USER" if body.suspended else "ACTIVATE_UNLOCK", uid
    )
    return {
        "message": "Account suspended."
        if body.suspended
        else "Account activated and unlocked."
    }


@router.delete("/users/{uid}")
def delete_user(
    uid: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    protect_admin(db, target, actor, True)
    audit(db, request, actor, "DELETE_USER", f"{target.username} (#{uid})")
    db.delete(target)
    return {"message": "User deleted."}


@router.post("/users/{uid}/reset")
def reset_user(
    uid: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if target.id == actor.id:
        raise HTTPException(409, "Change your own password in Profile.")
    link = create_reset(db, target)
    revoke_all(db, target)
    target.must_change = True
    target.failed = 0
    target.locked_until = None
    audit(db, request, actor, "PASSWORD_RESET_LINK", uid)
    return {
        "message": "One-time link expires in 30 minutes. Share it securely. Suspended users must also be activated.",
        "reset_link": link,
    }


@router.post("/users/{uid}/temporary-password")
def temporary(
    uid: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if target.id == actor.id:
        raise HTTPException(409, "Change your own password in Profile.")
    password = secrets.token_urlsafe(15)
    target.password_hash = hash_password(password)
    target.must_change = True
    target.failed = 0
    target.locked_until = None
    revoke_all(db, target)
    db.execute(update(Reset).where(Reset.user_id == uid).values(used=True))
    audit(db, request, actor, "TEMPORARY_PASSWORD", uid)
    return {
        "message": "Temporary password shown once. A change is required at login.",
        "temporary_password": password,
    }


@router.post("/users/{uid}/impersonate")
def impersonate(
    uid: int,
    request: Request,
    response: Response,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    target = require(db, User, uid)
    if (
        target.role == "ADMIN"
        or target.suspended
        or target.must_change
        or (target.locked_until and target.locked_until > now())
    ):
        raise HTTPException(
            409,
            "Impersonation requires an active USER with no forced password change or lock.",
        )
    audit(db, request, actor, "IMPERSONATE_START", f"{target.username} (#{uid})")
    csrf = issue(db, target, response, actor=actor, parent=request.state.session.id)
    return {"user": public_user(target), "csrf": csrf, "impersonating": True}


@router.post("/return")
def return_admin(
    request: Request,
    response: Response,
    user=Depends(identity),
    db=Depends(get_db, scope="function"),
):
    claims = request.state.claims
    if not claims.get("actor"):
        raise HTTPException(400, "No impersonation session.")
    actor = require(db, User, claims["actor"])
    request.state.session.revoked = True
    parent = db.get(Session, claims["parent"])
    parent.revoked = True
    audit(db, request, actor, "IMPERSONATE_END", user.id)
    csrf = issue(db, actor, response)
    return {"user": public_user(actor), "csrf": csrf, "impersonating": False}


@router.get("/audit")
def logs(
    offset: int = Query(0, ge=0),
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    return [
        {
            k: getattr(a, k)
            for k in ("id", "actor", "action", "target", "ip", "created_at")
        }
        for a in db.scalars(
            select(Audit).order_by(Audit.id.desc()).limit(100).offset(offset)
        )
    ]


@router.post("/sync")
def sync(request: Request, actor=Depends(admin), db=Depends(get_db, scope="function")):
    audit(db, request, actor, "SYNC_DATA", "football-data.org")
    db.commit()
    return refresh(db)


@router.post("/retrain")
def train(request: Request, actor=Depends(admin), db=Depends(get_db, scope="function")):
    report = retrain(db)
    audit(db, request, actor, "MODEL_CALIBRATION", report.get("version", "retained"))
    return report


@router.get("/settings")
def settings(actor=Depends(admin), db=Depends(get_db, scope="function")):
    name = db.get(Setting, "site_name")
    maintenance = db.get(Setting, "maintenance")
    key = db.get(Setting, "api_key")
    return {
        "site_name": name.value if name else "PredictPro",
        "maintenance": bool(maintenance and maintenance.value == "true"),
        "api_key_configured": bool(
            key.value if key else os.getenv("FOOTBALL_API_KEY", "")
        ),
    }


@router.put("/settings")
def edit_settings(
    body: SettingsInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    values = {"site_name": body.site_name, "maintenance": str(body.maintenance).lower()}
    if body.api_key is not None:
        values["api_key"] = body.api_key.strip()
    for key, value in values.items():
        setting = db.get(Setting, key)
        if setting:
            setting.value = value
        else:
            db.add(Setting(key=key, value=value))
    audit(db, request, actor, "UPDATE_SETTINGS", ",".join(values))
    return {
        "message": "Settings saved. API key is never returned. Protect database backups as secrets."
    }


@router.post("/leagues", status_code=201)
def create_league(
    body: LeagueInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    obj = League(**body.model_dump())
    db.add(obj)
    db.flush()
    audit(db, request, actor, "CREATE_LEAGUE", obj.id)
    return {"message": "League created.", "id": obj.id}


@router.put("/leagues/{pk}")
def edit_league(
    pk: int,
    body: LeagueInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    obj = require(db, League, pk)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    audit(db, request, actor, "EDIT_LEAGUE", pk)
    return {"message": "League updated."}


@router.delete("/leagues/{pk}")
def delete_league(
    pk: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    db.delete(require(db, League, pk))
    audit(db, request, actor, "DELETE_LEAGUE", pk)
    return {"message": "League deleted."}


@router.post("/teams", status_code=201)
def create_team(
    body: TeamInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    require(db, League, body.league_id)
    obj = Team(**body.model_dump())
    db.add(obj)
    db.flush()
    audit(db, request, actor, "CREATE_TEAM", obj.id)
    return {"message": "Team created.", "id": obj.id}


@router.put("/teams/{pk}")
def edit_team(
    pk: int,
    body: TeamInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    obj = require(db, Team, pk)
    require(db, League, body.league_id)
    for k, v in body.model_dump().items():
        setattr(obj, k, v)
    audit(db, request, actor, "EDIT_TEAM", pk)
    return {"message": "Team updated."}


@router.delete("/teams/{pk}")
def delete_team(
    pk: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    db.delete(require(db, Team, pk))
    audit(db, request, actor, "DELETE_TEAM", pk)
    return {"message": "Team deleted."}


def validate_match(db, body):
    require(db, League, body.league_id)
    for tid in (body.home_id, body.away_id):
        require(db, Team, tid)
    if body.status == "FINISHED" and body.kickoff > now():
        raise HTTPException(422, "A future match cannot be finished.")


@router.post("/matches", status_code=201)
def create_match(
    body: MatchInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    validate_match(db, body)
    m = Match(**body.model_dump(), source="manual")
    db.add(m)
    db.flush()
    if m.status == "SCHEDULED" and m.kickoff > now():
        get_prediction(db, m)
    audit(db, request, actor, "CREATE_MATCH", m.id)
    return {"message": "Match created.", "id": m.id}


@router.put("/matches/{pk}")
def edit_match(
    pk: int,
    body: MatchInput,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    m = require(db, Match, pk)
    validate_match(db, body)
    if (body.home_id, body.away_id, body.league_id) != (
        m.home_id,
        m.away_id,
        m.league_id,
    ):
        raise HTTPException(
            409,
            "To change participants or competition, delete and recreate the fixture.",
        )
    old_kickoff = m.kickoff
    for k, v in body.model_dump().items():
        setattr(m, k, v)
    p = db.scalar(select(Prediction).where(Prediction.match_id == pk))
    # A changed kickoff can never retroactively qualify a post-kickoff prediction.
    if p and body.kickoff != old_kickoff:
        p.eligible = p.eligible and p.created_at < body.kickoff
    if m.status == "FINISHED":
        notify_result(db, m)
    elif p:
        p.correct = None
        p.brier = None
    elif m.status == "SCHEDULED" and m.kickoff > now():
        get_prediction(db, m)
    audit(db, request, actor, "EDIT_MATCH", pk)
    return {
        "message": "Match updated; recorded results evaluated and followers notified."
    }


@router.delete("/matches/{pk}")
def delete_match(
    pk: int,
    request: Request,
    actor=Depends(admin),
    db=Depends(get_db, scope="function"),
):
    db.delete(require(db, Match, pk))
    audit(db, request, actor, "DELETE_MATCH", pk)
    return {"message": "Match deleted, including dependent picks and predictions."}
