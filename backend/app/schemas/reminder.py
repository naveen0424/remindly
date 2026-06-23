from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.reminder import TargetType


class ReminderTimeIn(BaseModel):
    due_at: datetime


class ReminderTimeOut(BaseModel):
    id: int
    due_at: datetime
    is_sent: bool

    class Config:
        from_attributes = True


class ReminderCreate(BaseModel):
    title: str
    body: Optional[str] = None
    target_type: TargetType = TargetType.self
    target_user_id: Optional[int] = None   # required if target_type = user
    group_id: Optional[int] = None          # required if target_type = group
    times: list[ReminderTimeIn]             # at least one time required


class ReminderUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    is_done: Optional[bool] = None
    times: Optional[list[ReminderTimeIn]] = None


class ReminderOut(BaseModel):
    id: int
    title: str
    body: Optional[str]
    target_type: TargetType
    target_user_id: Optional[int]
    group_id: Optional[int]
    is_done: bool
    created_at: datetime
    times: list[ReminderTimeOut]
    creator_id: int

    class Config:
        from_attributes = True
