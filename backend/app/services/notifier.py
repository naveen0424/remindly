from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.push_subscription import PushSubscription
from app.services.email import send_email
from app.services.push import send_push


def notify_user(db: Session, user_id: int, title: str, body: str, reminder_id: int = None):
    """
    Delivers a notification to one user via all three channels:
    1. In-app (stored in notifications table)
    2. Email
    3. Browser push (if subscribed)
    """
    # 1. In-app notification
    notif = Notification(
        user_id=user_id,
        reminder_id=reminder_id,
        title=title,
        body=body
    )
    db.add(notif)
    db.commit()

    # 2. Email
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        send_email(to=user.email, subject=title, body=body or title)

    # 3. Browser push — send to all registered devices for this user
    subs = db.query(PushSubscription).filter(PushSubscription.user_id == user_id).all()
    for sub in subs:
        send_push(
            subscription_info={
                "endpoint": sub.endpoint,
                "keys": {"p256dh": sub.p256dh, "auth": sub.auth}
            },
            title=title,
            body=body or title
        )


def notify_group(db: Session, group_id: int, title: str, body: str, reminder_id: int = None, exclude_user_id: int = None):
    """Notify all members of a group."""
    from app.models.group import GroupMember
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    for m in members:
        if m.user_id == exclude_user_id:
            continue
        notify_user(db, m.user_id, title, body, reminder_id)
