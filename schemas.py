import re
from typing import Optional

from pydantic import BaseModel, field_validator

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegistrationIn(BaseModel):
    name: str
    email: str
    college: Optional[str] = None
    department: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_ok(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name must not be empty")
        if len(v) > 100:
            raise ValueError("name must be at most 100 characters")
        return v

    @field_validator("email")
    @classmethod
    def email_ok(cls, v: str) -> str:
        v = v.strip().lower()
        if len(v) > 254 or not EMAIL_RE.match(v):
            raise ValueError("email is not a valid email address")
        return v

    @field_validator("college", "department")
    @classmethod
    def optional_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if len(v) > 150:
            raise ValueError("must be at most 150 characters")
        return v or None


class RegistrationOut(BaseModel):
    id: int
    name: str
    email: str
    college: Optional[str]
    department: Optional[str]
    registered_at: str
