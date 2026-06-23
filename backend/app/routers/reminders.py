from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.reminder import Reminder, ReminderTime, TargetType
from app.models.group import GroupMember
from app.schemas.reminder import ReminderCreate, ReminderUpdate, ReminderOut

router = APIRouter(prefix="/reminders", tags=["Reminders"])


def _validate_target(payload: ReminderCreate, db: Session, current_user: User):
    """Make sure target_user_id or group_id is provided when needed."""
    if payload.target_type == TargetType.user:
        if not payload.target_user_id:
            raise HTTPException(status_code=400, detail="target_user_id is required for target_type=user")
        target = db.query(User).filter(User.id == payload.target_user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target user not found")

    if payload.target_type == TargetType.group:
        if not payload.group_id:
            raise HTTPException(status_code=400, detail="group_id is required for target_type=group")
        membership = db.query(GroupMember).filter(
            GroupMember.group_id == payload.group_id,
            GroupMember.user_id == current_user.id
        ).first()
        if not membership:
            raise HTTPException(status_code=403, detail="You are not a member of this group")

    if not payload.times:
        raise HTTPException(status_code=400, detail="At least one reminder time is required")


@router.post("/", response_model=ReminderOut, status_code=status.HTTP_201_CREATED)
def create_reminder(
    payload: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _validate_target(payload, db, current_user)

    reminder = Reminder(
        title=payload.title,
        body=payload.body,
        creator_id=current_user.id,
        target_type=payload.target_type,
        target_user_id=payload.target_user_id if payload.target_type == TargetType.user else None,
        group_id=payload.group_id if payload.target_type == TargetType.group else None,
    )
    db.add(reminder)
    db.flush()  # get reminder.id before adding times

    for t in payload.times:
        db.add(ReminderTime(reminder_id=reminder.id, due_at=t.due_at))

    db.commit()
    db.refresh(reminder)
    return reminder


@router.get("/", response_model=list[ReminderOut])
def list_reminders(
    target_type: Optional[str] = None,
    is_done: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all reminders visible to the current user:
    - reminders they created
    - reminders sent to them directly
    - reminders sent to groups they belong to
    """
    # Get group IDs this user belongs to
    memberships = db.query(GroupMember.group_id).filter(
        GroupMember.user_id == current_user.id
    ).all()
    group_ids = [m.group_id for m in memberships]

    query = db.query(Reminder).filter(
        (Reminder.creator_id == current_user.id) |
        (Reminder.target_user_id == current_user.id) |
        (Reminder.group_id.in_(group_ids))
    )

    if target_type:
        query = query.filter(Reminder.target_type == target_type)
    if is_done is not None:
        query = query.filter(Reminder.is_done == is_done)

    return query.order_by(Reminder.created_at.desc()).all()


@router.get("/{reminder_id}", response_model=ReminderOut)
def get_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    # Check access
    memberships = db.query(GroupMember.group_id).filter(
        GroupMember.user_id == current_user.id
    ).all()
    group_ids = [m.group_id for m in memberships]

    has_access = (
        reminder.creator_id == current_user.id or
        reminder.target_user_id == current_user.id or
        reminder.group_id in group_ids
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")

    return reminder


@router.patch("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int,
    payload: ReminderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.creator_id == current_user.id  # only creator can edit
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found or not yours to edit")

    if payload.title is not None:
        reminder.title = payload.title
    if payload.body is not None:
        reminder.body = payload.body
    if payload.is_done is not None:
        reminder.is_done = payload.is_done

    # Replace times if provided
    if payload.times is not None:
        for t in reminder.times:
            db.delete(t)
        db.flush()
        for t in payload.times:
            db.add(ReminderTime(reminder_id=reminder.id, due_at=t.due_at))

    db.commit()
    db.refresh(reminder)
    return reminder


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    reminder = db.query(Reminder).filter(
        Reminder.id == reminder_id,
        Reminder.creator_id == current_user.id
    ).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found or not yours to delete")

    db.delete(reminder)
    db.commit()


@router.patch("/{reminder_id}/done", response_model=ReminderOut)
def mark_done(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Quick toggle — mark a reminder as done."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    # Anyone who can see it can mark it done
    memberships = db.query(GroupMember.group_id).filter(
        GroupMember.user_id == current_user.id
    ).all()
    group_ids = [m.group_id for m in memberships]

    has_access = (
        reminder.creator_id == current_user.id or
        reminder.target_user_id == current_user.id or
        reminder.group_id in group_ids
    )
    if not has_access:
        raise HTTPException(status_code=403, detail="Access denied")

    reminder.is_done = not reminder.is_done
    db.commit()
    db.refresh(reminder)
    return reminder
