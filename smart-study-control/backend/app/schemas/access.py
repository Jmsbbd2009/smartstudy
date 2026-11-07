from typing import Literal
from pydantic import Field
from app.schemas.contracts import Strict


class PasswordChange(Strict):
    current_password: str = Field(max_length=128)
    new_password: str = Field(min_length=12, max_length=128)


class StaffIn(Strict):
    login: str = Field(min_length=3, max_length=80, pattern=r"^[A-Za-z0-9_.+@-]+$")
    email: str | None = Field(default=None, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["TEACHER", "SCHOOL_ADMIN"]
    school_id: str | None = None
    school_name: str | None = Field(default=None, min_length=1, max_length=120)


class StaffState(Strict):
    active: bool


class LoginName(Strict):
    login: str = Field(min_length=1, max_length=254)


class PasswordProof(Strict):
    password: str = Field(max_length=128)


class ChallengeProof(Strict):
    challenge_id: str = Field(max_length=36)
    verifier: str = Field(min_length=30, max_length=100)


class OtpProof(ChallengeProof):
    code: str = Field(pattern=r"^\d{6}$")


class LinkProof(ChallengeProof):
    password: str = Field(max_length=128)


class PasskeyProof(ChallengeProof):
    credential: dict
    label: str = Field(default="Qurilma", min_length=1, max_length=100)


class TelegramPreference(Strict):
    enabled: bool


class Announcement(Strict):
    title: str = Field(min_length=1, max_length=150)
    body: str = Field(min_length=1, max_length=2000)
    recipient_ids: list[str] = Field(min_length=1, max_length=100)


class LocationPolicy(Strict):
    enabled: bool
    guardian_consent: Literal[True]
    max_minutes: int = Field(default=60, ge=1, le=240)


class LocationStart(Strict):
    minutes: int = Field(default=60, ge=1, le=240)
    sharing_consent: Literal[True]


class LocationPoint(Strict):
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    accuracy_m: float = Field(ge=0, le=100000, allow_inf_nan=False)
