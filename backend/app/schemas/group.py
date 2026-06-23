from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.group import MemberRole


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MemberOut(BaseModel):
    user_id: int
    role: MemberRole
    joined_at: datetime
    name: str
    email: str

    class Config:
        from_attributes = True


class GroupOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    creator_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupDetailOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    creator_id: int
    created_at: datetime
    members: list[MemberOut]

    class Config:
        from_attributes = True


class AddMemberRequest(BaseModel):
    user_id: int
