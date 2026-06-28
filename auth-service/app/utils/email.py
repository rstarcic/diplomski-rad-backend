import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def send_password_reset_email(
    to_email: str, token: str, full_name: str | None = None
) -> None:
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
    greeting = f"Hi {full_name}," if full_name else "Hi,"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your password"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    html = f"""
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8" />
      </head>
      <body style="margin:0; padding:0; background-color:#f4f4f4; font-family:Arial, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td align="center" style="padding:40px 0;">
              <table width="600" cellpadding="0" cellspacing="0"
                    style="background:#ffffff; border-radius:8px;
                            box-shadow:0 2px 8px rgba(0,0,0,0.08);">

                <tr>
                  <td style="background-color:#5b3fd6; padding:32px; text-align:center; border-radius:8px 8px 0 0;">
                    <h1 style="color:#ffffff; margin:0; font-size:24px;">WorkLink</h1>
                  </td>
                </tr>

                <tr>
                  <td style="padding:40px 32px;">
                    <p style="margin:0 0 8px; color:#1a1a1a; font-size:15px;">{greeting}</p>
                    <p style="margin:0 0 24px; color:#555555; font-size:15px; line-height:1.6;">
                      We received a request to reset your password.
                      Click the button below to setup a new one.
                      This link expires in <strong>15 minutes</strong>.
                    </p>
                    <table cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="border-radius:6px; background-color:#5b3fd6;">
                          <a href="{reset_link}"
                            style="display:inline-block; padding:14px 28px;
                                    color:#ffffff; text-decoration:none;
                                    font-size:15px; font-weight:bold;">
                            Reset password
                          </a>
                        </td>
                      </tr>
                    </table>
                    <p style="margin:24px 0 0; color:#999999; font-size:13px;">
                      If you didn't request this, you can safely ignore this email.
                      Your password won't change.
                    </p>
                  </td>
                </tr>

                <tr>
                  <td style="background-color:#f9f9f9; padding:20px 32px;
                            text-align:center; border-top:1px solid #eeeeee;
                            border-radius:0 0 8px 8px;">
                    <p style="margin:0; color:#aaaaaa; font-size:12px;">
                      &copy; 2026 WorkLink. All rights reserved.
                    </p>
                  </td>
                </tr>

              </table>
            </td>
          </tr>
        </table>
      </body>
      </html>
    """
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())


def _smtp_send(msg: MIMEMultipart, to_email: str) -> None:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())


def send_verification_email(
    to_email: str, token: str, full_name: str | None = None
) -> None:
    backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
    verify_link = f"{backend_url}/auth/verify-email?token={token}"
    greeting = f"Hi {full_name}," if full_name else "Hi,"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Verify your email address"
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><meta charset="UTF-8" /></head>
    <body style="margin:0; padding:0; background-color:#f4f4f4;
                 font-family:Arial, sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td align="center" style="padding:40px 0;">
            <table width="600" cellpadding="0" cellspacing="0"
                   style="background:#ffffff; border-radius:8px;
                          box-shadow:0 2px 8px rgba(0,0,0,0.08);">
              <tr>
                <td style="background-color:#5b3fd6; padding:32px;
                           text-align:center; border-radius:8px 8px 0 0;">
                  <h1 style="color:#ffffff; margin:0; font-size:24px;">
                    WorkLink
                  </h1>
                </td>
              </tr>
              <tr>
                <td style="padding:40px 32px;">
                  <p style="margin:0 0 8px; color:#1a1a1a; font-size:15px;">
                    {greeting}
                  </p>
                  <p style="margin:0 0 24px; color:#555555;
                            font-size:15px; line-height:1.6;">
                    Thanks for signing up! Please verify your email address
                    to activate your account.
                    This link expires in <strong>24 hours</strong>.
                  </p>
                  <table cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="border-radius:6px; background-color:#5b3fd6;">
                        <a href="{verify_link}"
                           style="display:inline-block; padding:14px 28px;
                                  color:#ffffff; text-decoration:none;
                                  font-size:15px; font-weight:bold;">
                          Verify email
                        </a>
                      </td>
                    </tr>
                  </table>
                  <p style="margin:24px 0 0; color:#999999; font-size:13px;">
                    If you did not create an account, you can ignore this email.
                  </p>
                </td>
              </tr>
              <tr>
                <td style="background-color:#f9f9f9; padding:20px 32px;
                           text-align:center; border-top:1px solid #eeeeee;
                           border-radius:0 0 8px 8px;">
                  <p style="margin:0; color:#aaaaaa; font-size:12px;">
                    &copy; 2026 WorkLink. All rights reserved.
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))
    _smtp_send(msg, to_email)
