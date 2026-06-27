"""PropelPay Email Service"""
import asyncio, logging, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

BRAND = "#6366f1"  # Indigo
DARK  = "#0f172a"

def _html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:{DARK};font-family:'Segoe UI',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
<tr><td align="center">
<table width="580" cellpadding="0" cellspacing="0"
 style="background:#1e293b;border-radius:16px;overflow:hidden;border:1px solid #334155;">
<tr><td style="background:linear-gradient(135deg,{BRAND},#8b5cf6);padding:28px;text-align:center;">
  <h1 style="margin:0;color:#fff;font-size:26px;font-weight:800;letter-spacing:1px;">PropelPay</h1>
  <p style="margin:4px 0 0;color:rgba(255,255,255,.8);font-size:12px;">Send. Sign. Get Paid.</p>
</td></tr>
<tr><td style="padding:32px 36px;color:#e2e8f0;font-size:15px;line-height:1.7;">{body}</td></tr>
<tr><td style="background:#0f172a;padding:20px;text-align:center;border-top:1px solid #1e293b;">
  <p style="margin:0;color:#64748b;font-size:12px;">© 2026 PropelPay · propelpay.io</p>
</td></tr>
</table></td></tr></table></body></html>"""

def _send(to: str, subject: str, html: str, text: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.warning(f"Email skipped (no SMTP config): {subject} → {to}")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = to
        msg.attach(MIMEText(text, "plain"))
        msg.attach(MIMEText(html, "html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.ehlo(); s.starttls(context=ctx); s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.SMTP_USER, to, msg.as_string())
        logger.info(f"Email sent: {subject} → {to}")
        return True
    except Exception as e:
        logger.error(f"SMTP error: {e}")
        return False

async def _async_send(to: str, subject: str, html: str, text: str) -> bool:
    return await asyncio.get_event_loop().run_in_executor(None, _send, to, subject, html, text)

async def send_welcome(to: str, name: str) -> bool:
    body = f"""
<h2 style="color:#fff;margin:0 0 8px;">Welcome to PropelPay, {name}! 🚀</h2>
<p style="color:#94a3b8;">You're now ready to send professional proposals and get paid faster.</p>
<h3 style="color:#fff;margin:24px 0 8px;">Your next steps:</h3>
<ol style="color:#e2e8f0;padding-left:20px;">
  <li style="margin-bottom:8px;">Add your first client</li>
  <li style="margin-bottom:8px;">Create an AI-powered proposal</li>
  <li style="margin-bottom:8px;">Send an invoice and get paid via Paystack</li>
</ol>
<div style="text-align:center;margin:32px 0;">
  <a href="{settings.FRONTEND_URL}/dashboard"
     style="background:linear-gradient(135deg,{BRAND},#8b5cf6);color:#fff;
            padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;">
    Open My Dashboard →
  </a>
</div>"""
    return await _async_send(to, f"Welcome to PropelPay, {name}! 🎉", _html("Welcome", body),
        f"Welcome to PropelPay {name}! Visit {settings.FRONTEND_URL}/dashboard to get started.")

async def send_proposal_notification(to: str, client_name: str, sender_name: str,
                                      proposal_title: str, view_url: str) -> bool:
    body = f"""
<h2 style="color:#fff;">You've received a proposal 📄</h2>
<p style="color:#94a3b8;">Hi {client_name}, {sender_name} has sent you a proposal.</p>
<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:20px;margin:20px 0;">
  <p style="margin:0;color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:1px;">Proposal</p>
  <p style="margin:4px 0 0;color:#fff;font-size:16px;font-weight:600;">{proposal_title}</p>
  <p style="margin:4px 0 0;color:#94a3b8;font-size:13px;">From: {sender_name}</p>
</div>
<div style="text-align:center;margin:28px 0;">
  <a href="{view_url}" style="background:linear-gradient(135deg,{BRAND},#8b5cf6);
     color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;">
    View & Sign Proposal →
  </a>
</div>"""
    return await _async_send(to, f"Proposal from {sender_name}: {proposal_title}",
        _html("New Proposal", body), f"You have a proposal from {sender_name}. View it: {view_url}")

async def send_invoice_notification(to: str, client_name: str, sender_name: str,
                                     invoice_number: str, amount: str, due_date: str,
                                     pay_url: str) -> bool:
    body = f"""
<h2 style="color:#fff;">Invoice from {sender_name} 💳</h2>
<p style="color:#94a3b8;">Hi {client_name}, here's your invoice.</p>
<div style="background:#0f172a;border:1px solid #334155;border-radius:12px;padding:24px;margin:20px 0;">
  <table width="100%">
    <tr><td style="color:#94a3b8;font-size:13px;">Invoice</td>
        <td style="color:#fff;font-weight:600;text-align:right;">{invoice_number}</td></tr>
    <tr><td style="color:#94a3b8;font-size:13px;padding-top:8px;">Amount Due</td>
        <td style="color:#6366f1;font-size:22px;font-weight:800;text-align:right;">{amount}</td></tr>
    <tr><td style="color:#94a3b8;font-size:13px;padding-top:8px;">Due Date</td>
        <td style="color:#f87171;font-weight:600;text-align:right;">{due_date}</td></tr>
  </table>
</div>
<div style="text-align:center;margin:28px 0;">
  <a href="{pay_url}" style="background:linear-gradient(135deg,#10b981,#059669);
     color:#fff;padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:800;font-size:16px;">
    Pay Now →
  </a>
</div>"""
    return await _async_send(to, f"Invoice {invoice_number} — {amount} due {due_date}",
        _html("Invoice", body), f"Invoice {invoice_number} for {amount}. Pay at: {pay_url}")

async def send_payment_received(to: str, business_name: str, amount: str, invoice_number: str) -> bool:
    body = f"""
<h2 style="color:#3fb950;">Payment Received ✅</h2>
<p style="color:#94a3b8;">Great news! A payment has been received.</p>
<div style="background:#0f172a;border:1px solid #3fb950;border-radius:12px;padding:20px;margin:20px 0;">
  <p style="margin:0;color:#3fb950;font-size:24px;font-weight:800;">{amount}</p>
  <p style="margin:4px 0 0;color:#94a3b8;font-size:13px;">Invoice: {invoice_number}</p>
</div>
<p style="color:#e2e8f0;">The payment has been recorded in your PropelPay dashboard.</p>"""
    return await _async_send(to, f"💰 Payment received — {amount}",
        _html("Payment Received", body), f"Payment of {amount} received for invoice {invoice_number}.")

async def send_payment_reminder(to: str, client_name: str, business_name: str,
                                 invoice_number: str, amount: str, days_overdue: int,
                                 pay_url: str, custom_message: str = "") -> bool:
    urgency_color = "#f87171" if days_overdue > 14 else "#fbbf24"
    body = f"""
<h2 style="color:{urgency_color};">Payment Reminder ⚠️</h2>
<p style="color:#94a3b8;">Hi {client_name},</p>
<p style="color:#e2e8f0;">{custom_message or f'This is a friendly reminder that invoice {invoice_number} for {amount} is {days_overdue} days overdue.'}</p>
<div style="background:#0f172a;border:1px solid {urgency_color};border-radius:12px;padding:20px;margin:20px 0;">
  <p style="margin:0;color:#94a3b8;font-size:12px;">Amount Overdue</p>
  <p style="margin:4px 0 0;color:{urgency_color};font-size:22px;font-weight:800;">{amount}</p>
  <p style="margin:4px 0 0;color:#94a3b8;font-size:13px;">Invoice: {invoice_number} · {days_overdue} days overdue</p>
</div>
<div style="text-align:center;margin:24px 0;">
  <a href="{pay_url}" style="background:{urgency_color};color:#0f172a;
     padding:14px 36px;border-radius:8px;text-decoration:none;font-weight:800;">
    Pay Now →
  </a>
</div>
<p style="color:#64748b;font-size:13px;">— {business_name}</p>"""
    subject = f"⚠️ {'FINAL NOTICE: ' if days_overdue > 30 else ''}Invoice {invoice_number} — Payment Overdue ({days_overdue} days)"
    return await _async_send(to, subject, _html("Payment Reminder", body),
        f"Invoice {invoice_number} is {days_overdue} days overdue. Pay at: {pay_url}")
