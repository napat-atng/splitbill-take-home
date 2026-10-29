"""Public API schemas, separate from database table models."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strict=True, strip_whitespace=True, min_length=1)]
Username = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=64)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EqualSplit(InputModel):
    type: Literal["equal"]
    members: Annotated[list[Username], Field(min_length=1)]


class ExactSplit(InputModel):
    type: Literal["exact"]
    shares: Annotated[dict[Username, Annotated[str, Field(strict=True)]], Field(min_length=1)]


class ExpenseCreate(InputModel):
    description: Annotated[NonEmptyText, Field(max_length=500)]
    paid_by: Username
    amount: Annotated[str, Field(strict=True)]
    split: Annotated[EqualSplit | ExactSplit, Field(discriminator="type")]


class GroupSummary(BaseModel):
    id: int
    name: str


class GroupDetail(GroupSummary):
    members: list[str]


class SplitRead(BaseModel):
    type: Literal["equal", "exact"]
    shares: dict[str, str]


class ExpenseRead(BaseModel):
    id: int
    group_id: int
    description: str
    paid_by: str
    amount: str
    split: SplitRead
    created_at: datetime
    is_deleted: bool


class BalancesRead(BaseModel):
    group_id: int
    balances: dict[str, str]


class ErrorDetail(BaseModel):
    location: list[str | int]
    message: str
    type: str


class ErrorInfo(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorRead(BaseModel):
    error: ErrorInfo
