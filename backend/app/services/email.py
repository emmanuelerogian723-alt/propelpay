"""
PropelPay Email Service v2
Primary: Resend API (transactional, reliable, free 3k/month)
Fallback: SMTP (Gmail/Brevo/any)
Features: retry queue, delivery logging, beautiful HTML templates
"""
import asyncio, logging, smtplib, ssl, json, traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import httpx
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

BRAND  = "#6366f1"
BRAND2 = "#8b5cf6"
GREEN  = "#10b981"
DARK   = "#0f172a"
CARD   = "#1e293b"
TEXT   = "#e2e8f0"
MUTED  = "#94a3b8"

# ─── HTML template engine ────────────────────────────────────────────────────

def _wrap(title: str, body: str, preheader: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:{DARK};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:{TEXT}}}
  .wrapper{{max-width:600px;margin:0 auto;padding:40px 16px}}
  .card{{background:{CARD};border-radius:16px;overflow:hidden;border:1px solid #334155}}
  .header{{background:linear-gradient(135deg,{BRAND},{BRAND2});padding:32px;text-align:center}}
  .logo{{font-size:28px;font-weight:900;color:#fff;letter-spacing:1px}}
  .tagline{{color:rgba(255,255,255,.75);font-size:13px;margin-top:6px}}
  .body{{padding:36px}}
  .footer{{background:{DARK};padding:24px;text-align:center;border-top:1px solid #1e293b}}
  .footer p{{color:#475569;font-size:12px;line-height:1.6}}
  h1{{color:#fff;font-size:22px;font-weight:700;margin-bottom:8px}}
  h2{{color:#fff;font-size:18px;font-weight:600;margin-bottom:8px}}
  p{{color:{MUTED};font-size:14px;line-height:1.7;margin-bottom:12px}}
  .highlight{{color:#fff}}
  .box{{background:{DARK};border-radius:12px;padding:20px;margin:20px 0;border:1px solid #334155}}
  .box-green{{border-color:{GREEN}}}
  .box-red{{border-color:#ef4444}}
  .amount{{font-size:28px;font-weight:800;color:{BRAND};display:block;margin:6px 0}}
  .amount-green{{color:{GREEN}}}
  .label{{font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}}
  .btn{{display:inline-block;padding:14px 32px;border-radius:10px;text-decoration:none;
         font-weight:700;font-size:15px;margin-top:8px}}
  .btn-primary{{background:linear-gradient(135deg,{BRAND},{BRAND2});color:#fff}}
  .btn-green{{background:linear-gradient(135deg,{GREEN},#059669);color:#fff}}
  .btn-warn{{background:#f59e0b;color:{DARK}}}
  .row{{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #1e293b}}
  .row:last-child{{border-bottom:none}}
  .row-label{{color:{MUTED};font-size:13px}}
  .row-val{{color:#fff;font-size:13px;font-weight:600}}
  .steps{{counter-reset:step;padding:0}}
  .step{{counter-increment:step;display:flex;align-items:flex-start;gap:14px;margin-bottom:14px}}
  .step::before{{content:counter(step);background:rgba(99,102,241,.25);color:{BRAND};
                  min-width:28px;height:28px;border-radius:50%;display:flex;align-items:center;
                  justify-content:center;font-weight:700;font-size:12px;margin-top:2px}}
  .step-text{{color:{TEXT};font-size:14px;line-height:1.6}}
  table.items{{width:100%;border-collapse:collapse;margin:16px 0}}
  table.items th{{background:{DARK};color:{MUTED};font-size:11px;text-transform:uppercase;
                   letter-spacing:.8px;padding:10px 12px;text-align:left}}
  table.items td{{padding:10px 12px;color:{TEXT};font-size:13px;border-bottom:1px solid #334155}}
  table.items tr:last-child td{{border-bottom:none}}
  .center{{text-align:center}}
  .mt{{margin-top:24px}}
</style>
</head>
<body>
{"<span style='display:none;max-height:0;overflow:hidden'>"+preheader+"</span>" if preheader else ""}
<div class="wrapper">
  <div class="card">
    <div class="header">
      <div class="logo">⚡ PropelPay</div>
      <div class="tagline">Send. Sign. Get Paid.</div>
    </div>
    <div class="body">{body}</div>
    <div class="footer">
      <p>© 2026 PropelPay · Professional Invoicing for Modern Businesses</p>
      <p style="margin-top:4px">Questions? Email us at support@propelpay.io</p>
    </div>
  </div>
</div>
</body></html>"""


# ─── Resend API sender ────────────────────────────────────────────────────────

async def _send_resend(to: str, subject: str, html: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Returns (success, message_id, error_msg)"""
    if not settings.RESEND_API_KEY:
        return False, None, "no_resend_key"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}",
                         "Content-Type": "application/json"},
                json={"from": f"{settings.SMTP_FROM_NAME} <{settings.RESEND_FROM_EMAIL or 'noreply@propelpay.io'}>",
                      "to": [to], "subject": subject, "html": html}
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("id"):
                logger.info(f"Resend OK: {subject} → {to} [{data['id']}]")
                return True, data["id"], None
            err = data.get("message") or data.get("error", {}).get("message", "Unknown Resend error")
            logger.warning(f"Resend failed: {err}")
            return False, None, err
    except Exception as e:
        logger.error(f"Resend exception: {e}")
        return False, None, str(e)


def _send_smtp_sync(to: str, subject: str, html: str, text: str) -> tuple[bool, Optional[str]]:
    """Sync SMTP send. Returns (success, error_msg)"""
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False, "no_smtp_config"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = to
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.ehlo(); s.starttls(context=ctx)
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.SMTP_USER, to, msg.as_string())
        logger.info(f"SMTP OK: {subject} → {to}")
        return True, None
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return False, str(e)


async def _send_smtp(to: str, subject: str, html: str, text: str) -> tuple[bool, Optional[str]]:
    return await asyncio.get_event_loop().run_in_executor(None, _send_smtp_sync, to, subject, html, text)


async def send_email(
    to: str,
    subject: str,
    html: str,
    text: str = "",
    email_type: str = "general",
    user_id: Optional[str] = None,
    invoice_id: Optional[str] = None,
    proposal_id: Optional[str] = None,
    retries: int = 3,
) -> dict:
    """
    Main dispatcher with retry logic and DB logging.
    Returns {success, provider, message_id, error}
    """
    from app.database import AsyncSessionLocal
    from app.models.email_log import EmailLog

    log = EmailLog(
        user_id=user_id, invoice_id=invoice_id,
        proposal_id=proposal_id, to_email=to,
        subject=subject, email_type=email_type,
        status="queued", provider="resend"
    )

    success = False
    provider = "none"
    message_id = None
    error_msg = None

    for attempt in range(retries):
        if attempt > 0:
            await asyncio.sleep(2 ** attempt)  # exponential backoff

        # Try Resend first
        if settings.RESEND_API_KEY:
            ok, mid, err = await _send_resend(to, subject, html)
            if ok:
                success, provider, message_id = True, "resend", mid
                break
            error_msg = err
            # Only retry on network errors, not auth/config errors
            if err in ("no_resend_key",) or "api_key" in str(err).lower():
                break

        # Fallback to SMTP
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            ok, err = await _send_smtp(to, subject, html, text or _html_to_text(html))
            if ok:
                success, provider = True, "smtp"
                break
            error_msg = err
        else:
            if not settings.RESEND_API_KEY:
                logger.warning(f"Email skipped (no config): {subject} → {to}")
                error_msg = "no_email_provider_configured"
                break

    # Log to DB (non-blocking)
    asyncio.create_task(_log_email(log, success, provider, message_id, error_msg))
    return {"success": success, "provider": provider, "message_id": message_id, "error": error_msg}


async def _log_email(log, success: bool, provider: str, message_id: Optional[str], error: Optional[str]):
    try:
        from app.database import AsyncSessionLocal
        log.status = "sent" if success else "failed"
        log.provider = provider
        log.resend_id = message_id
        log.error_msg = error
        async with AsyncSessionLocal() as db:
            db.add(log)
            await db.commit()
    except Exception as e:
        logger.error(f"Email log DB error: {e}")


def _html_to_text(html: str) -> str:
    import re
    text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    return ' '.join(text.split())


# ─── Email builders ───────────────────────────────────────────────────────────

async def send_welcome(to: str, name: str, user_id: str = None) -> dict:
    body = f"""
<h1>Welcome, {name}! 🚀</h1>
<p>You're now set up on PropelPay — the smartest way to send proposals, invoice clients, and get paid faster.</p>
<div class="box mt">
  <p class="label">Get started in 3 steps</p>
  <ol class="steps">
    <li class="step"><span class="step-text"><strong style="color:#fff">Add your first client</strong> — go to the Clients tab and enter their name and email.</span></li>
    <li class="step"><span class="step-text"><strong style="color:#fff">Create an AI proposal</strong> — let PropelPay write a professional proposal in seconds.</span></li>
    <li class="step"><span class="step-text"><strong style="color:#fff">Send an invoice</strong> — attach a Paystack payment link and get paid instantly.</span></li>
  </ol>
</div>
<div class="center mt">
  <a class="btn btn-primary" href="{settings.FRONTEND_URL}/dashboard">Open My Dashboard →</a>
</div>"""
    return await send_email(to, f"Welcome to PropelPay, {name}! ⚡",
        _wrap("Welcome", body, f"You're all set, {name}. Let's get you paid faster."),
        f"Welcome to PropelPay, {name}! Open your dashboard: {settings.FRONTEND_URL}/dashboard",
        email_type="welcome", user_id=user_id)


async def send_invoice_email(
    to: str, client_name: str, sender_name: str,
    invoice_number: str, amount: str, due_date: str,
    items: list, pay_url: str,
    user_id: str = None, invoice_id: str = None
) -> dict:
    rows = ""
    for item in items:
        rows += f"""<tr><td>{item.get('description','')}</td>
                    <td style="text-align:center">{item.get('quantity',1)}</td>
                    <td style="text-align:right">{amount.split()[0]} {item.get('unit_price',0):,.2f}</td>
                    <td style="text-align:right;font-weight:600;color:#fff">{amount.split()[0]} {item.get('total',0):,.2f}</td>
                    </tr>"""

    body = f"""
<h1>Invoice from {sender_name} 💳</h1>
<p>Hi <span class="highlight">{client_name}</span>, please find your invoice below. Payment is due by <strong style="color:#f87171">{due_date}</strong>.</p>
<div class="box">
  <div class="row"><span class="row-label">Invoice Number</span><span class="row-val">{invoice_number}</span></div>
  <div class="row"><span class="row-label">From</span><span class="row-val">{sender_name}</span></div>
  <div class="row"><span class="row-label">Due Date</span><span class="row-val" style="color:#f87171">{due_date}</span></div>
  <div class="row"><span class="row-label">Total Due</span><span class="row-val" style="font-size:20px;color:{BRAND}">{amount}</span></div>
</div>
{"<table class='items'><thead><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Total</th></tr></thead><tbody>"+rows+"</tbody></table>" if items else ""}
<div class="center mt">
  <a class="btn btn-green" href="{pay_url}">Pay {amount} Now →</a>
</div>
<p style="margin-top:16px;font-size:12px;text-align:center">Secure payment powered by Paystack</p>"""

    return await send_email(
        to, f"Invoice {invoice_number} — {amount} due {due_date}",
        _wrap("Invoice", body, f"Invoice {invoice_number} for {amount} from {sender_name}."),
        f"Invoice {invoice_number} — {amount} — Pay now: {pay_url}",
        email_type="invoice", user_id=user_id, invoice_id=invoice_id
    )


async def send_proposal_email(
    to: str, client_name: str, sender_name: str,
    proposal_title: str, view_url: str, preview_text: str = "",
    user_id: str = None, proposal_id: str = None
) -> dict:
    body = f"""
<h1>You've received a proposal 📄</h1>
<p>Hi <span class="highlight">{client_name}</span>, {sender_name} has sent you a proposal.</p>
<div class="box">
  <p class="label">Proposal Title</p>
  <h2>{proposal_title}</h2>
  <p>From: <strong style="color:#fff">{sender_name}</strong></p>
  {"<p style='margin-top:8px'>"+preview_text+"</p>" if preview_text else ""}
</div>
<div class="center mt">
  <a class="btn btn-primary" href="{view_url}">View & Sign Proposal →</a>
</div>
<p style="margin-top:16px;font-size:12px;text-align:center;color:#475569">This link expires in 30 days</p>"""

    return await send_email(
        to, f"Proposal from {sender_name}: {proposal_title}",
        _wrap("Proposal", body, f"{sender_name} sent you a proposal. Review and sign it."),
        f"Proposal from {sender_name}: {proposal_title}. View: {view_url}",
        email_type="proposal", user_id=user_id, proposal_id=proposal_id
    )


async def send_payment_received(
    to: str, business_name: str, amount: str,
    invoice_number: str, user_id: str = None, invoice_id: str = None
) -> dict:
    body = f"""
<h1>Payment Received ✅</h1>
<p>Great news — a payment has just been recorded on your account.</p>
<div class="box box-green">
  <p class="label">Amount Received</p>
  <span class="amount amount-green">{amount}</span>
  <p style="margin-top:4px">Invoice: <strong style="color:#fff">{invoice_number}</strong></p>
</div>
<p>This has been logged in your <a href="{settings.FRONTEND_URL}/dashboard" style="color:{BRAND}">PropelPay dashboard</a>.</p>"""

    return await send_email(
        to, f"💰 Payment received — {amount}",
        _wrap("Payment Received", body, f"You just received {amount} for invoice {invoice_number}."),
        f"Payment of {amount} received for invoice {invoice_number}.",
        email_type="payment_received", user_id=user_id, invoice_id=invoice_id
    )


async def send_payment_reminder(
    to: str, client_name: str, business_name: str,
    invoice_number: str, amount: str, days_overdue: int,
    pay_url: str, custom_message: str = "",
    user_id: str = None, invoice_id: str = None
) -> dict:
    urgency_class = "box-red" if days_overdue > 14 else "box"
    warn_color = "#ef4444" if days_overdue > 14 else "#f59e0b"
    final_notice = days_overdue > 30
    subject_prefix = "🔴 FINAL NOTICE: " if final_notice else ("⚠️ " if days_overdue > 0 else "")

    body = f"""
<h1 style="color:{warn_color}">{subject_prefix}Payment Reminder ⚠️</h1>
<p>Hi <span class="highlight">{client_name}</span>,</p>
<p>{custom_message or f"This is a friendly reminder that invoice <strong>{invoice_number}</strong> for <strong>{amount}</strong> is {'<strong style=color:{warn_color}>' + str(days_overdue) + ' days overdue</strong>' if days_overdue > 0 else 'due soon'}."}</p>
<div class="{urgency_class}">
  <p class="label">Amount {'Overdue' if days_overdue > 0 else 'Due'}</p>
  <span class="amount" style="color:{warn_color}">{amount}</span>
  <p>Invoice: <strong style="color:#fff">{invoice_number}</strong>{f" · {days_overdue} days overdue" if days_overdue > 0 else ""}</p>
</div>
<div class="center mt">
  <a class="btn {'btn-warn' if days_overdue > 0 else 'btn-green'}" href="{pay_url}">Pay Now →</a>
</div>
<p style="margin-top:16px;font-size:12px;text-align:center">— {business_name}</p>"""

    return await send_email(
        to,
        f"{subject_prefix}Invoice {invoice_number} — {amount}{f' ({days_overdue} days overdue)' if days_overdue > 0 else ' due soon'}",
        _wrap("Payment Reminder", body),
        f"Invoice {invoice_number} for {amount}. Pay at: {pay_url}",
        email_type="reminder", user_id=user_id, invoice_id=invoice_id
    )


# Backward-compat aliases
send_welcome_email = send_welcome
send_invoice_notification = send_invoice_email
send_proposal_notification = send_proposal_email
