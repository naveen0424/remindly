from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.reminder import Reminder, ReminderTime, TargetType
from app.services.notifier import notify_user, notify_group

scheduler = BackgroundScheduler(timezone="UTC")


def fire_due_reminders():
    """Runs every minute. Finds unsent reminder times that are due and dispatches notifications."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        due_times = db.query(ReminderTime).filter(
            ReminderTime.due_at <= now,
            ReminderTime.is_sent == False  # noqa: E712
        ).all()

        for rt in due_times:
            reminder = rt.reminder
            if not reminder:
                continue

            title = f"🔔 {reminder.title}"
            body = reminder.body or ""

            if reminder.target_type == TargetType.self:
                notify_user(db, reminder.creator_id, title, body, reminder.id)

            elif reminder.target_type == TargetType.user and reminder.target_user_id:
                # Notify both creator and target user
                notify_user(db, reminder.target_user_id, title, body, reminder.id)
                if reminder.target_user_id != reminder.creator_id:
                    notify_user(db, reminder.creator_id, f"Reminder sent to user: {reminder.title}", body, reminder.id)

            elif reminder.target_type == TargetType.group and reminder.group_id:
                notify_group(db, reminder.group_id, title, body, reminder.id)

            # Mark as sent
            rt.is_sent = True
            db.commit()
            print(f"[SCHEDULER] Fired reminder_time {rt.id} for reminder '{reminder.title}'")

    except Exception as e:
        print(f"[SCHEDULER ERROR] {e}")
    finally:
        db.close()


def start_scheduler():
    scheduler.add_job(fire_due_reminders, "interval", minutes=1, id="fire_reminders")
    scheduler.start()
    print("[SCHEDULER] Started — checking reminders every minute")


def stop_scheduler():
    scheduler.shutdown()
