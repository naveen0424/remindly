import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_email(to: str, subject: str, body: str):
    """Send a plain-text email via SMTP. Silently skips if SMTP not configured."""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"[EMAIL SKIP] No SMTP config. Would send to {to}: {subject}")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAILS_FROM
        msg["To"] = to

        html = f"""
        <html><body style="font-family:sans-serif;padding:24px;color:#1a1a18">
          <h2 style="color:#4F6AF5">🔔 {subject}</h2>
          <p>{body}</p>
          <hr style="border:none;border-top:1px solid #e8e7e3;margin:24px 0"/>
          <p style="color:#9e9e99;font-size:13px">Sent by Remindly</p>
        </body></html>
        """
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM, to, msg.as_string())

        print(f"[EMAIL SENT] To: {to} | Subject: {subject}")

    except Exception as e:
        print(f"[EMAIL ERROR] {e}")
