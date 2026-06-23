from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class TargetType(str, enum.Enum):
    self = "self"           # reminder for yourself only
    user = "user"           # reminder for a specific user
    group = "group"         # reminder for an entire group


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)

    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Who is this reminder for?
    target_type = Column(Enum(TargetType), nullable=False, default=TargetType.self)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)   # set if target_type = user
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)        # set if target_type = group

    is_done = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="created_reminders", foreign_keys=[creator_id])
    target_user = relationship("User", foreign_keys=[target_user_id])
    group = relationship("Group", back_populates="reminders")
    times = relationship("ReminderTime", back_populates="reminder", cascade="all, delete-orphan")


class ReminderTime(Base):
    """
    One reminder can have multiple due times.
    e.g. remind me at 9am, 2pm, and 6pm for the same note.
    """
    __tablename__ = "reminder_times"

    id = Column(Integer, primary_key=True, index=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    is_sent = Column(Boolean, default=False)

    # Relationships
    reminder = relationship("Reminder", back_populates="times")
