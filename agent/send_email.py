# agent/send_email.py
# PURPOSE: Action layer of the agent.
# Takes the digest dict from run_agent.py and emails it to you.
# Uses Gmail SMTP — completely free, no external service needed.

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

GMAIL_USER     = os.getenv("GMAIL_USER")       # yourname@gmail.com
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")   # 16-char app password
DIGEST_EMAIL   = os.getenv("DIGEST_EMAIL")     # where to send digest


def format_email_body(digest: dict) -> str:
    """
    Converts the JSON digest into readable plain text email.
    Plain text is intentional — works in every email client,
    no HTML rendering issues, loads instantly.
    """

    divider  = "─" * 50
    today    = digest.get("date", date.today().isoformat())

    lines = []

    # ── Header ───────────────────────────────────────────
    lines.append("🌅  AI MORNING DIGEST")
    lines.append(f"📅  {today}")
    lines.append(divider)

    # ── Summary ──────────────────────────────────────────
    lines.append("\n📌  TODAY'S OVERVIEW")
    lines.append(divider)
    lines.append(digest.get("summary", "No summary available."))

    # ── Products ─────────────────────────────────────────
    lines.append("\n\n🚀  PRODUCT LAUNCHES & UPDATES")
    lines.append(divider)
    for i, item in enumerate(digest.get("products", []), 1):
        lines.append(f"\n{i}. {item['title']}")
        lines.append(f"   {item['summary']}")
        lines.append(f"   Source : {item.get('source', 'N/A')}")
        if item.get("url"):
            lines.append(f"   Link   : {item['url']}")

    # ── Research ─────────────────────────────────────────
    lines.append("\n\n📄  RESEARCH PAPERS")
    lines.append(divider)
    for i, item in enumerate(digest.get("research", []), 1):
        lines.append(f"\n{i}. {item['title']}")
        lines.append(f"   {item['summary']}")
        if item.get("authors"):
            lines.append(f"   Authors: {item['authors']}")
        if item.get("url"):
            lines.append(f"   Link   : {item['url']}")

    # ── Industry ─────────────────────────────────────────
    lines.append("\n\n🏢  INDUSTRY NEWS")
    lines.append(divider)
    for i, item in enumerate(digest.get("industry", []), 1):
        lines.append(f"\n{i}. {item['title']}")
        lines.append(f"   {item['summary']}")
        lines.append(f"   Source : {item.get('source', 'N/A')}")
        if item.get("url"):
            lines.append(f"   Link   : {item['url']}")

    # ── Concept of the Day ───────────────────────────────
    concept = digest.get("concept_of_the_day", {})
    if concept:
        lines.append("\n\n💡  CONCEPT OF THE DAY")
        lines.append(divider)
        lines.append(f"\n📖  {concept.get('title', '')}")
        lines.append(f"\n{concept.get('explanation', '')}")
        lines.append(f"\n🔗  Why today: {concept.get('why_today', '')}")

    # ── Footer ───────────────────────────────────────────
    lines.append(f"\n\n{divider}")
    lines.append("⚡  Sent by your AI Agent")
    lines.append("🛠   Built with Groq (llama-3.3-70b) + GitHub Actions")
    lines.append("📚  Sources: VentureBeat, TechCrunch, OpenAI, Anthropic,")
    lines.append("    Indian Express, The Neuron Daily, Papers With Code,")
    lines.append("    Slogix, Uber Blog, AI Weekly")
    lines.append(divider)

    return "\n".join(lines)


def send_digest_email(digest: dict) -> None:
    """
    Builds and sends the digest email via Gmail SMTP.
    
    Agent concept: this is the "action" — the agent's
    only side effect on the real world.
    """

    # Build the email object
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🌅 AI Digest — {digest.get('date', date.today().isoformat())}"
    msg["From"]    = f"AI Digest Agent <{GMAIL_USER}>"
    msg["To"]      = DIGEST_EMAIL

    # Format and attach the body
    body = format_email_body(digest)
    msg.attach(MIMEText(body, "plain"))

    # Send via Gmail SMTP
    # Port 587 = TLS (secure), always use this over port 25
    print(f"📧 Sending email to {DIGEST_EMAIL}...")
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()           # identify ourselves to the server
        server.starttls()       # upgrade connection to encrypted TLS
        server.login(GMAIL_USER, GMAIL_APP_PASS)
        server.sendmail(GMAIL_USER, DIGEST_EMAIL, msg.as_string())

    print("✅ Email sent successfully!")


# ── Quick test: run this file directly with a fake digest ────────────
# Command: python agent/send_email.py
if __name__ == "__main__":
    # Import and run the full agent to get real digest
    from run_agent import run_agent
    digest = run_agent()
    send_digest_email(digest)