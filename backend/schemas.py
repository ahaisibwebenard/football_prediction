from datetime import datetime, timezone
from typing import Literal
import re
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator


class Profile(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    username: str = Field(pattern=r"^[a-zA-Z0-9_]{3,30}$")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        if "<" in v or ">" in v or not v.strip():
            raise ValueError("Use plain text for names.")
        return v.strip()

    @field_validator("email", "username")
    @classmethod
    def lower(cls, v):
        return str(v).lower()


class Signup(Profile):
    password: str = Field(min_length=10, max_length=72)


class Login(BaseModel):
    login: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class Password(BaseModel):
    current_password: str = Field(max_length=72)
    password: str = Field(min_length=10, max_length=72)


class Forgot(BaseModel):
    email: EmailStr


class ResetInput(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(min_length=10, max_length=72)


class UserCreate(Signup):
    role: Literal["ADMIN", "USER"] = "USER"


class UserEdit(Profile):
    role: Literal["ADMIN", "USER"] = "USER"


class StateInput(BaseModel):
    suspended: bool


class PickInput(BaseModel):
    outcome: Literal["Home", "Draw", "Away"]


class LeagueInput(BaseModel):
    name: str = Field(min_length=2, max_length=100, pattern=r"^[^<>]+$")
    code: str = Field(pattern=r"^[A-Z0-9_]{2,12}$")


class TeamInput(BaseModel):
    name: str = Field(min_length=2, max_length=100, pattern=r"^[^<>]+$")
    league_id: int = Field(gt=0)


class MatchInput(BaseModel):
    league_id: int = Field(gt=0)
    home_id: int = Field(gt=0)
    away_id: int = Field(gt=0)
    kickoff: datetime
    status: Literal["SCHEDULED", "FINISHED", "POSTPONED", "CANCELLED"] = "SCHEDULED"
    home_goals: int | None = Field(default=None, ge=0, le=50)
    away_goals: int | None = Field(default=None, ge=0, le=50)

    @model_validator(mode="after")
    def consistent(self):
        if self.kickoff.tzinfo is None:
            raise ValueError("Kickoff must include a timezone.")
        self.kickoff = self.kickoff.astimezone(timezone.utc).replace(tzinfo=None)
        if self.home_id == self.away_id:
            raise ValueError("Teams must differ.")
        if self.status == "FINISHED" and (
            self.home_goals is None or self.away_goals is None
        ):
            raise ValueError("Finished matches require both scores.")
        if self.status != "FINISHED" and (
            self.home_goals is not None or self.away_goals is not None
        ):
            raise ValueError("Scores are only accepted for finished matches.")
        return self


class SettingsInput(BaseModel):
    site_name: str = Field(min_length=2, max_length=60, pattern=r"^[^<>]+$")
    maintenance: bool
    api_key: str | None = Field(default=None, max_length=150)
