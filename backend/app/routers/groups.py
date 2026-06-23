from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.group import Group, GroupMember, MemberRole
from app.schemas.group import GroupCreate, GroupUpdate, GroupOut, GroupDetailOut, MemberOut, AddMemberRequest

router = APIRouter(prefix="/groups", tags=["Groups"])


def _require_admin(group_id: int, user_id: int, db: Session):
    """Raise 403 if user is not admin of the group."""
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    if not membership or membership.role != MemberRole.admin:
        raise HTTPException(status_code=403, detail="Only group admins can do this")
    return membership


def _require_member(group_id: int, user_id: int, db: Session):
    """Raise 403 if user is not a member of the group."""
    membership = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    return membership


def _build_member_out(m: GroupMember) -> MemberOut:
    return MemberOut(
        user_id=m.user_id,
        role=m.role,
        joined_at=m.joined_at,
        name=m.user.name,
        email=m.user.email
    )


@router.post("/", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(
    payload: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = Group(
        name=payload.name,
        description=payload.description,
        creator_id=current_user.id
    )
    db.add(group)
    db.flush()

    # Creator is automatically admin
    db.add(GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role=MemberRole.admin
    ))
    db.commit()
    db.refresh(group)
    return group


@router.get("/", response_model=list[GroupOut])
def list_my_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns all groups the current user belongs to."""
    memberships = db.query(GroupMember).filter(
        GroupMember.user_id == current_user.id
    ).all()
    group_ids = [m.group_id for m in memberships]
    return db.query(Group).filter(Group.id.in_(group_ids)).all()


@router.get("/{group_id}", response_model=GroupDetailOut)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    _require_member(group_id, current_user.id, db)

    members = [_build_member_out(m) for m in group.members]
    return GroupDetailOut(
        id=group.id,
        name=group.name,
        description=group.description,
        creator_id=group.creator_id,
        created_at=group.created_at,
        members=members
    )


@router.patch("/{group_id}", response_model=GroupOut)
def update_group(
    group_id: int,
    payload: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    _require_admin(group_id, current_user.id, db)

    if payload.name is not None:
        group.name = payload.name
    if payload.description is not None:
        group.description = payload.description

    db.commit()
    db.refresh(group)
    return group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    _require_admin(group_id, current_user.id, db)

    db.delete(group)
    db.commit()


@router.post("/{group_id}/members", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def add_member(
    group_id: int,
    payload: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _require_admin(group_id, current_user.id, db)

    # Check user exists
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check not already a member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == payload.user_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")

    member = GroupMember(
        group_id=group_id,
        user_id=payload.user_id,
        role=MemberRole.member
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _build_member_out(member)


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    _require_admin(group_id, current_user.id, db)

    # Admin cannot remove themselves
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Admin cannot remove themselves — delete the group instead")

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    db.delete(member)
    db.commit()


@router.patch("/{group_id}/members/{user_id}/promote", response_model=MemberOut)
def promote_to_admin(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Promote a member to admin — like WhatsApp group admin promotion."""
    _require_admin(group_id, current_user.id, db)

    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.role = MemberRole.admin
    db.commit()
    db.refresh(member)
    return _build_member_out(member)


@router.post("/{group_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Any member can leave. Admin must promote someone else first."""
    membership = _require_member(group_id, current_user.id, db)

    if membership.role == MemberRole.admin:
        # Check if there's another admin
        other_admin = db.query(GroupMember).filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id != current_user.id,
            GroupMember.role == MemberRole.admin
        ).first()
        if not other_admin:
            raise HTTPException(
                status_code=400,
                detail="You are the only admin. Promote another member before leaving."
            )

    db.delete(membership)
    db.commit()
