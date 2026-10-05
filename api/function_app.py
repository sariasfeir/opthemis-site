"""
OpThemis — lead capture API

A single Azure Function backing the public get-started landing page
(index.html at the site root). Kept intentionally small: this repo exists
only to host that page and this one endpoint, decoupled from the main
OpThemis product codebase.
"""
import azure.functions as func
import json
import logging
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


# ─────────────────────────────────────────
# 4. LEAD CAPTURE  —  public landing page signup (/get-started)
# ─────────────────────────────────────────
# Objective : Receive {name, email, company, interest, message} from the
#             public get-started.html form and notify Saria by email.
#             Includes a honeypot field ("website") to silently drop bot
#             submissions without giving them a signal.
# Input     : POST JSON body
#               name      (str, optional)
#               email     (str, required) — validated with a simple regex
#               company   (str, optional)
#               interest  (str, optional) — e.g. "More info" / "Schedule a call"
#               message   (str, optional)
#               website   (str, optional) — honeypot; must be empty
# Output    : 200 {"status": "ok"} on success or silently-dropped spam
#             400 {"error": "..."} on invalid input
#             500 {"error": "..."} if the notification email could not be sent
# Requires  : Azure Function App Settings (or api/local.settings.json for
#             local dev) — none of these are committed to the repo:
#               SMTP_HOST        e.g. smtp.gmail.com / smtp.sendgrid.net
#               SMTP_PORT        default 587
#               SMTP_USERNAME
#               SMTP_PASSWORD    an app password / API key, never your main password
#               NOTIFY_TO_EMAIL  defaults to saria.sfeir@opthemis.ch if unset
#             Until these are set, the endpoint returns 500 — the form tells
#             the visitor to email Saria directly in that case.
import re
import smtplib
from email.message import EmailMessage

_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

@app.route(route="lead_capture", methods=["POST"])
def lead_capture(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("lead_capture called")
    try:
        body = req.get_json()
    except Exception:
        return func.HttpResponse(
            json.dumps({"error": "invalid JSON body"}),
            mimetype="application/json", status_code=400
        )

    # Honeypot: real visitors never fill this hidden field in.
    if (body.get("website") or "").strip():
        logging.info("lead_capture: honeypot triggered, dropping silently")
        return func.HttpResponse(json.dumps({"status": "ok"}), mimetype="application/json")

    email = (body.get("email") or "").strip()
    if not _EMAIL_RE.match(email):
        return func.HttpResponse(
            json.dumps({"error": "a valid email is required"}),
            mimetype="application/json", status_code=400
        )

    name     = (body.get("name") or "").strip()[:200]
    company  = (body.get("company") or "").strip()[:200]
    interest = (body.get("interest") or "").strip()[:100]
    message  = (body.get("message") or "").strip()[:2000]

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_pass = os.environ.get("SMTP_PASSWORD")
    notify_to = os.environ.get("NOTIFY_TO_EMAIL", "saria.sfeir@opthemis.ch")

    if not (smtp_host and smtp_user and smtp_pass):
        logging.error("lead_capture: SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD not configured")
        return func.HttpResponse(
            json.dumps({"error": "email notification not configured"}),
            mimetype="application/json", status_code=500
        )

    msg = EmailMessage()
    msg["Subject"] = f"OpThemis lead: {name or email}" + (f" ({company})" if company else "")
    msg["From"] = smtp_user
    msg["To"] = notify_to
    if email:
        msg["Reply-To"] = email
    msg.set_content(
        f"New signup from the get-started page\n\n"
        f"Name:     {name or '(not given)'}\n"
        f"Email:    {email}\n"
        f"Company:  {company or '(not given)'}\n"
        f"Interest: {interest or '(not given)'}\n"
        f"Message:  {message or '(none)'}\n"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
    except Exception as e:
        logging.error(f"lead_capture: failed to send notification email: {e}")
        return func.HttpResponse(
            json.dumps({"error": "failed to send notification"}),
            mimetype="application/json", status_code=500
        )

    return func.HttpResponse(json.dumps({"status": "ok"}), mimetype="application/json")
