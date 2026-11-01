from datetime import datetime, timezone
from sqlalchemy import (
    String,
    Integer,
    Float,
    Boolean,
    Text,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(10), default="USER")
    suspended: Mapped[bool] = mapped_column(Boolean, default=False)
    must_change: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    locked_until: Mapped[datetime | None]
    failed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=now)
    last_active: Mapped[datetime] = mapped_column(default=now)
    __table_args__ = (CheckConstraint("role IN ('ADMIN','USER')"),)


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    csrf: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime]
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Reset(Base):
    __tablename__ = "resets"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime]
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    code: Mapped[str] = mapped_column(String(12), unique=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Team(Base):
    __tablename__ = "teams"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="RESTRICT")
    )
    external_id: Mapped[int | None] = mapped_column(unique=True)


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[int | None] = mapped_column(unique=True)
    league_id: Mapped[int] = mapped_column(
        ForeignKey("leagues.id", ondelete="RESTRICT")
    )
    home_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"))
    away_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="RESTRICT"))
    kickoff: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(16), default="SCHEDULED")
    home_goals: Mapped[int | None]
    away_goals: Mapped[int | None]
    source: Mapped[str] = mapped_column(String(20), default="manual")
    __table_args__ = (
        CheckConstraint("home_id != away_id"),
        CheckConstraint("status IN ('SCHEDULED','FINISHED','POSTPONED','CANCELLED')"),
    )


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), unique=True
    )
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=now)
    model_version: Mapped[str] = mapped_column(String(80))
    eligible: Mapped[bool] = mapped_column(Boolean, default=True)
    correct: Mapped[bool | None]
    brier: Mapped[float | None] = mapped_column(Float)


class Pick(Base):
    __tablename__ = "picks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    outcome: Mapped[str] = mapped_column(String(4))
    created_at: Mapped[datetime] = mapped_column(default=now)
    __table_args__ = (
        UniqueConstraint("user_id", "match_id"),
        CheckConstraint("outcome IN ('Home','Draw','Away')"),
    )


class Favorite(Base):
    __tablename__ = "favorites"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )


class Follow(Base):
    __tablename__ = "follows"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    match_id: Mapped[int] = mapped_column(
        ForeignKey("matches.id", ondelete="CASCADE"), primary_key=True
    )


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(300))
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=now)
    __table_args__ = (UniqueConstraint("user_id", "match_id"),)


class Audit(Base):
    __tablename__ = "audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(60))
    target: Mapped[str] = mapped_column(String(100))
    ip: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(default=now)


class Setting(Base):
    __tablename__ = "settings"
    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(Text)


class RateBucket(Base):
    __tablename__ = "rate_buckets"
    key: Mapped[str] = mapped_column(String(100), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    started: Mapped[datetime] = mapped_column(default=now)
