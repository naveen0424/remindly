from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class NotificationOut(BaseModel):
    id: int
    user_id: int
    reminder_id: Optional[int]
    title: str
    body: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PushSubscriptionIn(BaseModel):
    endpoint: str
    p256dh: str
    auth: str
