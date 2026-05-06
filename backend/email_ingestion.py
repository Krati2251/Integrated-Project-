"""
Email Ingestion Service — Polls Gmail for unread emails and sends them
to the Finance Support Triage Agent API for automated processing.

Usage:
    python email_ingestion.py

Prerequisites:
    1. Enable IMAP in Gmail:  Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
    2. Generate an App Password:  Google Account → Security → 2-Step Verification → App passwords
       (Use the 16-character app password as EMAIL_PASSWORD, NOT your regular Gmail password)
    3. Set EMAIL_USER and EMAIL_PASSWORD in the .env file.
"""

import os
import sys
import time
import email
import imaplib
import logging
import requests
from pathlib import Path
from email.header import decode_header
from dotenv import load_dotenv

# Load .env from project root BEFORE using os.getenv()
_project_root = Path(__file__).parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)

# -------------------- Configuration --------------------

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993
MAILBOX = "INBOX"

API_ENDPOINT = "http://127.0.0.1:8001/process_ticket"
POLL_INTERVAL = 10  # seconds
FETCH_ALL = os.getenv("EMAIL_FETCH_ALL", "false").lower() == "true"
INCLUDE_SENT = os.getenv("EMAIL_INCLUDE_SENT", "false").lower() == "true"
LOOKBACK_DAYS = int(os.getenv("EMAIL_LOOKBACK_DAYS", "30"))

# -------------------- Logging --------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("email_ingestion")

# -------------------- Helper Functions --------------------


def validate_credentials():
    """Check that email credentials are set before starting."""
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.error(
            "EMAIL_USER and EMAIL_PASSWORD must be set in the .env file.\n"
            "Example:\n"
            "  EMAIL_USER=yourname@gmail.com\n"
            "  EMAIL_PASSWORD=abcd efgh ijkl mnop    (Gmail App Password)\n"
        )
        sys.exit(1)


def connect_to_gmail() -> imaplib.IMAP4_SSL:
    """Establish an SSL connection to Gmail's IMAP server and log in."""
    logger.info(f"📧 Connecting to {IMAP_SERVER} as {EMAIL_USER}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL_USER, EMAIL_PASSWORD)
    mail.select(MAILBOX)
    logger.info("✅ Connected and INBOX selected.")
    return mail


def decode_mime_header(header_value: str) -> str:
    """Decode a MIME-encoded header (Subject, From, etc.) into a plain string."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    parts = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            parts.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            parts.append(part)
    return " ".join(parts)


def extract_body(msg: email.message.Message) -> str:
    """
    Extract the plain-text body from an email message.

    Walks the MIME tree and returns the first text/plain part.
    Falls back to text/html (stripped of tags) if no plain-text part exists.
    """
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition:
                continue

            if content_type == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break  # prefer plain text

            elif content_type == "text/html" and not body:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    html = payload.decode(charset, errors="replace")
                    # Basic HTML tag stripping (good enough for triage)
                    import re
                    body = re.sub(r"<[^>]+>", " ", html)
                    body = re.sub(r"\s+", " ", body).strip()
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")

    return body.strip()


def send_to_api(email_body: str, subject: str, sender: str) -> dict | None:
    """
    Send the email data to the /process_ticket API endpoint.

    The API expects {"email_body": "..."} — we prepend the subject and
    sender to give the AI more context.
    """
    # Compose a rich text block for the AI to analyse
    full_text = (
        f"From: {sender}\n"
        f"Subject: {subject}\n"
        f"\n"
        f"{email_body}"
    )

    try:
        resp = requests.post(
            API_ENDPOINT,
            json={"email_body": full_text},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        logger.error("⚠️  Cannot connect to the API. Is the FastAPI server running?")
        return None
    except requests.Timeout:
        logger.error("⚠️  API request timed out.")
        return None
    except requests.HTTPError as e:
        logger.error(f"⚠️  API returned an error: {e.response.status_code} — {e.response.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"⚠️  Unexpected error sending to API: {e}")
        return None


def mark_as_read(mail: imaplib.IMAP4_SSL, email_id: bytes):
    """Flag an email as Seen so it won't be fetched again."""
    mail.store(email_id, "+FLAGS", "\\Seen")


def process_unread_emails(mail: imaplib.IMAP4_SSL):
    """Search for new emails, extract data, and forward to the API."""
    if FETCH_ALL:
        from datetime import datetime as _dt, timedelta as _td
        since_date = (_dt.now() - _td(days=LOOKBACK_DAYS)).strftime("%d-%b-%Y")
        criteria = f'(SINCE "{since_date}")'
        mailboxes = ["INBOX", "[Gmail]/Sent Mail", "[Gmail]/All Mail"]
    else:
        criteria = "UNSEEN"
        mailboxes = ["INBOX"]
        if INCLUDE_SENT:
            mailboxes.extend(["[Gmail]/Sent Mail", "[Gmail]/All Mail"])

    email_ids = []
    for mailbox in mailboxes:
        try:
            status, _ = mail.select(mailbox)
            if status != "OK":
                continue
            status, messages = mail.search(None, criteria)
            if status == "OK":
                email_ids.extend((mailbox, eid) for eid in messages[0].split())
        except Exception as e:
            logger.warning(f"Could not search mailbox {mailbox}: {e}")

    if not email_ids:
        return  # no new emails — silent

    logger.info(f"📬 Found {len(email_ids)} unread email(s). Processing...")

    for mailbox, email_id in email_ids:
        try:
            # Fetch the email
            mail.select(mailbox)
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                logger.warning(f"  Could not fetch email ID {email_id}")
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Extract fields
            subject = decode_mime_header(msg.get("Subject", "(No Subject)"))
            sender = decode_mime_header(msg.get("From", "(Unknown Sender)"))
            body = extract_body(msg)

            logger.info(f"  ────────────────────────────────────────")
            logger.info(f"  📩 From:    {sender}")
            logger.info(f"  📌 Subject: {subject}")
            logger.info(f"  📝 Body:    {body[:120]}{'...' if len(body) > 120 else ''}")

            if not body or len(body.strip()) < 10:
                logger.warning("  ⚠️  Email body too short, skipping.")
                mark_as_read(mail, email_id)
                continue

            # Send to API
            result = send_to_api(body, subject, sender)

            if result:
                ticket_id = result.get("ticket_id", "N/A")
                priority = result.get("analysis", {}).get("priority", "N/A")
                category = result.get("analysis", {}).get("category", "N/A")
                logger.info(f"  ✅ Ticket created: {ticket_id[:8]}... | Priority: {priority} | Category: {category}")
            else:
                logger.warning("  ⚠️  Failed to process via API (will retry next cycle).")
                continue  # don't mark as read — retry next loop

            # Mark as read only after successful processing
            mark_as_read(mail, email_id)
            logger.info(f"  ✔️  Marked as read.")

        except Exception as e:
            logger.error(f"  ❌ Error processing email ID {email_id}: {e}")
            continue  # don't crash — move to next email


# -------------------- Main Loop --------------------


def main():
    """Run the email ingestion loop."""
    validate_credentials()

    logger.info("=" * 60)
    logger.info("  FINANCE SUPPORT TRIAGE — EMAIL INGESTION SERVICE")
    logger.info("=" * 60)
    logger.info(f"  Account:       {EMAIL_USER}")
    logger.info(f"  IMAP Server:   {IMAP_SERVER}:{IMAP_PORT}")
    logger.info(f"  API Endpoint:  {API_ENDPOINT}")
    logger.info(f"  Poll Interval: {POLL_INTERVAL}s")
    logger.info("=" * 60)

    mail = None

    while True:
        try:
            # (Re)connect if needed
            if mail is None:
                mail = connect_to_gmail()

            # Keep the connection alive & process
            mail.noop()
            process_unread_emails(mail)

        except imaplib.IMAP4.abort:
            logger.warning("🔌 IMAP connection aborted. Reconnecting...")
            mail = None

        except imaplib.IMAP4.error as e:
            logger.error(f"🔌 IMAP error: {e}. Reconnecting...")
            mail = None

        except ConnectionError:
            logger.warning("🌐 Network connection lost. Retrying in 30s...")
            mail = None
            time.sleep(30)
            continue

        except KeyboardInterrupt:
            logger.info("\n👋 Shutting down gracefully...")
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass
            sys.exit(0)

        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}. Retrying in 15s...")
            mail = None
            time.sleep(15)
            continue

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
