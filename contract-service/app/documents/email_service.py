import os
import smtplib
from pathlib import Path

from dotenv import load_dotenv

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape


load_dotenv(Path(__file__).resolve().parents[2] / ".env")

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


class ContractEmailError(Exception):
    pass


def send_contract_email(
    *,
    to_email: str,
    pdf_content: bytes,
    contract_number: str,
    job_title: str,
    client_name: str,
    contractor_name: str,
    recipient_name: str,
    starts_at: str | None,
    ends_at: str | None,
) -> None:
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ContractEmailError("SMTP is not configured.")

    values = {
        "recipient": escape(recipient_name),
        "number": escape(contract_number),
        "job": escape(job_title),
        "client": escape(client_name),
        "contractor": escape(contractor_name),
        "start": escape(starts_at) if starts_at else "To be confirmed",
        "end": escape(ends_at) if ends_at else "To be confirmed",
    }
    msg = MIMEMultipart("mixed")
    msg["Subject"] = f"Your signed WorkLink contract - {contract_number}"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    html = f"""
    <!DOCTYPE html><html lang="en"><body style="margin:0;background:#f4f4f4;font-family:Arial,sans-serif">
      <table width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:40px 12px">
        <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#fff;border-radius:8px">
          <tr><td style="background:#5b3fd6;padding:32px;text-align:center;border-radius:8px 8px 0 0">
            <h1 style="color:#fff;margin:0;font-size:24px">WorkLink</h1>
            <p style="color:#ded8ff;margin:8px 0 0">Your signed contract</p>
          </td></tr>
          <tr><td style="padding:36px 32px;color:#555;font-size:15px;line-height:1.6">
            <p style="color:#1a1a1a">Hello {values['recipient']},</p>
            <p>The signed WorkLink contract you requested is attached as a PDF. Please keep it for your records.</p>
            <table width="100%" cellpadding="8" cellspacing="0" style="background:#f8f7ff;border-left:3px solid #5b3fd6;color:#333;font-size:14px">
              <tr><td><strong>Contract</strong></td><td>{values['number']}</td></tr>
              <tr><td><strong>Job</strong></td><td>{values['job']}</td></tr>
              <tr><td><strong>Status</strong></td><td>Active</td></tr>
              <tr><td><strong>Client</strong></td><td>{values['client']}</td></tr>
              <tr><td><strong>Contractor</strong></td><td>{values['contractor']}</td></tr>
              <tr><td><strong>Start date</strong></td><td>{values['start']}</td></tr>
              <tr><td><strong>End date</strong></td><td>{values['end']}</td></tr>
            </table>
            <p style="margin-top:24px;color:#999;font-size:13px">This email was sent because you requested a copy through WorkLink.</p>
          </td></tr>
          <tr><td style="background:#f9f9f9;padding:20px;text-align:center;color:#aaa;font-size:12px">&copy; 2026 WorkLink. All rights reserved.</td></tr>
        </table>
      </td></tr></table>
    </body></html>
    """
    msg.attach(MIMEText(html, "html", "utf-8"))
    attachment = MIMEApplication(pdf_content, _subtype="pdf")
    attachment.add_header(
        "Content-Disposition",
        "attachment",
        filename=f"WorkLink-Contract-{contract_number}.pdf",
    )
    msg.attach(attachment)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except smtplib.SMTPResponseException as exc:
      error = exc.smtp_error.decode(errors="replace")
      raise ContractEmailError(
          f"Google SMTP error {exc.smtp_code}: {error}"
      ) from exc

    except (OSError, smtplib.SMTPException) as exc:
        raise ContractEmailError(
            f"SMTP connection error: {type(exc).__name__}: {exc}"
        ) from exc