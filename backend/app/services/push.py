import json
from app.core.config import settings


def send_push(subscription_info: dict, title: str, body: str):
    """Send a browser push notification. Skips if VAPID keys not configured."""
    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        print(f"[PUSH SKIP] No VAPID config. Would push: {title}")
        return

    try:
        from pywebpush import webpush, WebPushException
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"title": title, "body": body}),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL}
        )
        print(f"[PUSH SENT] {title}")
    except Exception as e:
        print(f"[PUSH ERROR] {e}")
