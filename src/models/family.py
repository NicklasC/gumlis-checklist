from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


FAMILY_MEMBERS = ("Nicklas", "Ida", "Thor", "Johanna")
FAMILY_ASSIGNEES = ("Alla",) + FAMILY_MEMBERS
FAMILY_ACTORS = FAMILY_MEMBERS + ("Automatik", "Nicklas (Sheet)")


class FamilyTaskStatus(str, Enum):
    CURRENT = "Aktuell"
    LATER = "Senare"
    COMPLETED = "Klar"
    DELETED = "Raderad"


class FamilyTask(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str
    title: str
    status: FamilyTaskStatus
    assignee: str = "Alla"
    assigned_by: str
    assigned_at: datetime
    created_by: str
    created_at: datetime
    deadline: Optional[date] = None
    updated_by: str
    updated_at: datetime
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    version: int = Field(ge=1)

    @field_validator("id", "title")
    @classmethod
    def _required_text(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("Värdet får inte vara tomt")
        return normalized

    @field_validator("assignee")
    @classmethod
    def _valid_assignee(cls, value: str) -> str:
        if value not in FAMILY_ASSIGNEES:
            raise ValueError("Okänd ansvarig")
        return value

    @field_validator("assigned_by", "created_by")
    @classmethod
    def _valid_member(cls, value: str) -> str:
        if value not in FAMILY_MEMBERS:
            raise ValueError("Okänd familjemedlem")
        return value

    @field_validator("updated_by")
    @classmethod
    def _valid_actor(cls, value: str) -> str:
        if value not in FAMILY_ACTORS:
            raise ValueError("Okänd ändringsaktör")
        return value

    @field_validator("completed_by")
    @classmethod
    def _valid_completer(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in FAMILY_MEMBERS:
            raise ValueError("Okänd utförare")
        return value

    @model_validator(mode="after")
    def _completion_fields_match_status(self):
        is_complete = self.status == FamilyTaskStatus.COMPLETED
        has_completion = self.completed_by is not None and self.completed_at is not None
        if is_complete != has_completion:
            raise ValueError("Slutförandefält stämmer inte med status")
        return self


class FamilyTaskDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    assignee: str = "Alla"
    deadline: Optional[date] = None

    @field_validator("title")
    @classmethod
    def _required_title(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("Uppgiften får inte vara tom")
        if len(normalized) > 200:
            raise ValueError("Uppgiften är för lång")
        return normalized

    @field_validator("assignee")
    @classmethod
    def _valid_assignee(cls, value: str) -> str:
        if value not in FAMILY_ASSIGNEES:
            raise ValueError("Okänd ansvarig")
        return value


class FamilyMember(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    active: bool
    sort_order: int = Field(ge=0)

    @field_validator("name")
    @classmethod
    def _known_member(cls, value: str) -> str:
        if value not in FAMILY_MEMBERS:
            raise ValueError("Okänd familjemedlem")
        return value


class FamilyFavorite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    active: bool
    sort_order: int = Field(ge=0)

    @field_validator("id", "title")
    @classmethod
    def _required_text(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("Värdet får inte vara tomt")
        return normalized


class FamilyRowIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet: str
    row: int = Field(ge=2)
    error: str


class FamilyBootstrap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[FamilyTask]
    members: list[FamilyMember]
    favorites: list[FamilyFavorite]
    invalid_rows: list[FamilyRowIssue] = Field(default_factory=list)
    server_time: datetime


class FamilyTaskPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tasks: list[FamilyTask]
    invalid_rows: list[FamilyRowIssue] = Field(default_factory=list)
    server_time: datetime


@dataclass(frozen=True)
class FamilyConnection:
    device_token: str
    member: str

    def __post_init__(self):
        if len(self.device_token) < 32:
            raise ValueError("Enhetsnyckeln är för kort")
        if self.member not in FAMILY_MEMBERS:
            raise ValueError("Okänd familjemedlem")
