import smtplib
from email.mime.text import MIMEText
import os

def send_verification_email(email: str, token: str):
    verify_link = f"https://grammrlyst.in/auth/verify-email?token={token}"

    msg = MIMEText(f"""
    Hi 👋

    Please verify your email by clicking the link below:

    {verify_link}

    If you didn't create this account, ignore this mail.
    """)
    msg["Subject"] = "Verify your email - Grammrlyst"
    msg["From"] = "noreply@grammrlyst.in"
    msg["To"] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(
        os.getenv("SMTP_EMAIL"),
        os.getenv("SMTP_PASSWORD")
    )
    server.send_message(msg)
    server.quit()

def send_reset_password_email(email: str, token: str):
    reset_link = f"https://grammrlyst.in/auth/reset-password?token={token}"

    msg = MIMEText(f"""
    Hi 👋

    You requested a password reset.

    Click the link below to set a new password:
    {reset_link}

    This link will expire in 15 minutes.

    If you didn’t request this, ignore this email.
    """)
    msg["Subject"] = "Reset your password - Grammrlyst"
    msg["From"] = "noreply@grammrlyst.in"
    msg["To"] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(
        os.getenv("SMTP_EMAIL"),
        os.getenv("SMTP_PASSWORD")
    )
    server.send_message(msg)
    server.quit()