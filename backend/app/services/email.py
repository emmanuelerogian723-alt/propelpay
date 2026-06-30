"""PropelPay Email Service v3 — Fixed Resend sender + proper status logging"""
import asyncio, logging, smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
import httpx
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

BRAND="#7c3aed"; BRAND2="#6d28d9"; GREEN="#10b981"; DARK="#07000f"; CARD="#0d0019"; TEXT="#e2e8f0"; MUTED="#94a3b8"

def _wrap(title:str, body:str)->str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:{DARK};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:{TEXT}}}
.w{{max-width:600px;margin:0 auto;padding:36px 16px}}.card{{background:{CARD};border-radius:16px;overflow:hidden;border:1px solid rgba(255,255,255,.07)}}
.hdr{{background:linear-gradient(135deg,{BRAND},{BRAND2});padding:28px;text-align:center}}.logo{{font-size:26px;font-weight:900;color:#fff}}.tag{{color:rgba(255,255,255,.7);font-size:12px;margin-top:5px}}
.bdy{{padding:32px}}.ftr{{background:{DARK};padding:20px;text-align:center;border-top:1px solid rgba(255,255,255,.05)}}
.ftr p{{color:#475569;font-size:11px;line-height:1.6}}h1{{color:#fff;font-size:20px;font-weight:700;margin-bottom:7px}}
p{{color:{MUTED};font-size:13px;line-height:1.7;margin-bottom:10px}}.hl{{color:#fff}}.box{{background:{DARK};border-radius:10px;padding:18px;margin:16px 0;border:1px solid rgba(255,255,255,.07)}}
.amt{{font-size:26px;font-weight:800;color:{BRAND};display:block;margin:5px 0}}.amt-g{{color:{GREEN}}}.lbl{{font-size:10px;color:{MUTED};text-transform:uppercase;letter-spacing:1px;margin-bottom:3px}}
.btn{{display:inline-block;padding:13px 28px;border-radius:9px;text-decoration:none;font-weight:700;font-size:14px;margin-top:7px}}
.btn-p{{background:linear-gradient(135deg,{BRAND},{BRAND2});color:#fff}}.btn-g{{background:linear-gradient(135deg,{GREEN},#059669);color:#fff}}
.row{{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04)}}.row:last-child{{border-bottom:none}}
.rl{{color:{MUTED};font-size:12px}}.rv{{color:#fff;font-size:12px;font-weight:600}}
table.it{{width:100%;border-collapse:collapse;margin:14px 0}}table.it th{{background:{DARK};color:{MUTED};font-size:10px;text-transform:uppercase;letter-spacing:.8px;padding:9px 10px;text-align:left}}
table.it td{{padding:9px 10px;color:{TEXT};font-size:12px;border-bottom:1px solid rgba(255,255,255,.04)}}
</style></head><body><div class="w"><div class="card">
<div class="hdr"><div class="logo">⚡ PropelPay</div><div class="tag">Send. Sign. Get Paid.</div></div>
<div class="bdy">{body}</div>
<div class="ftr"><p>© 2026 PropelPay by MUTYINT · Professional Invoicing for Africa</p>
<p style="margin-top:3px">Questions? WhatsApp: +234 704 556 0291 · multipurposetalentedyounginven@gmail.com</p></div>
</div></div></body></html>"""


async def _send_resend(to:str, subject:str, html:str)->(bool,Optional[str],Optional[str]):
    if not settings.RESEND_API_KEY:
        return False, None, "no_resend_key"
    # Use onboarding@resend.dev when no custom domain configured (works without domain verification)
    from_email = settings.RESEND_FROM_EMAIL if settings.RESEND_FROM_EMAIL else "onboarding@resend.dev"
    from_name  = settings.SMTP_FROM_NAME or "PropelPay"
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization":f"Bearer {settings.RESEND_API_KEY}","Content-Type":"application/json"},
                json={"from":f"{from_name} <{from_email}>","to":[to],"subject":subject,"html":html}
            )
            if resp.status_code in (200,201):
                data = resp.json()
                mid = data.get("id")
                if mid:
                    logger.info(f"Resend OK: {subject} → {to} [{mid}]")
                    return True, mid, None
            err_data = resp.json()
            err = err_data.get("message") or err_data.get("name","Resend error")
            logger.warning(f"Resend HTTP {resp.status_code}: {err} | from={from_email}")
            return False, None, f"resend_{resp.status_code}:{err}"
    except Exception as e:
        logger.error(f"Resend exception: {e}")
        return False, None, str(e)


def _send_smtp_sync(to:str,subject:str,html:str,text:str)->(bool,Optional[str]):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False, "no_smtp_config"
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"]=subject; msg["From"]=f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL or settings.SMTP_USER}>"; msg["To"]=to
        msg.attach(MIMEText(text,"plain")); msg.attach(MIMEText(html,"html"))
        ctx = ssl.create_default_context()
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.ehlo(); s.starttls(context=ctx); s.login(settings.SMTP_USER,settings.SMTP_PASSWORD); s.sendmail(settings.SMTP_USER,to,msg.as_string())
        logger.info(f"SMTP OK: {subject} → {to}")
        return True, None
    except Exception as e:
        logger.error(f"SMTP error: {e}"); return False, str(e)


async def _send_smtp(to,subject,html,text):
    return await asyncio.get_event_loop().run_in_executor(None,_send_smtp_sync,to,subject,html,text)


async def send_email(to:str,subject:str,html:str,text:str="",email_type:str="general",
                     user_id:str=None,invoice_id:str=None,proposal_id:str=None,retries:int=2)->dict:
    success=False; provider="none"; message_id=None; error_msg=None

    for attempt in range(retries):
        if attempt>0: await asyncio.sleep(2**attempt)
        # Try Resend
        if settings.RESEND_API_KEY:
            ok,mid,err = await _send_resend(to,subject,html)
            if ok: success,provider,message_id=True,"resend",mid; break
            error_msg=err
            if err and ("invalid_api_key" in str(err).lower() or "401" in str(err)): break
        # Try SMTP fallback
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            ok,err = await _send_smtp(to,subject,html,text or _html_to_text(html))
            if ok: success,provider=True,"smtp"; break
            error_msg=err
        else:
            if not settings.RESEND_API_KEY:
                logger.warning(f"No email config — skipping: {subject} → {to}")
                error_msg="no_email_provider_configured"; break

    # Log (non-blocking)
    asyncio.create_task(_log_email(email_type,to,subject,success,provider,message_id,error_msg,user_id,invoice_id,proposal_id))
    if not success:
        logger.error(f"Email FAILED after {retries} attempts: {subject} → {to} | error={error_msg}")
    return {"success":success,"provider":provider,"message_id":message_id,"error":error_msg}


async def _log_email(email_type,to,subject,success,provider,message_id,error,user_id,invoice_id,proposal_id):
    try:
        from app.database import AsyncSessionLocal
        from app.models.email_log import EmailLog
        log = EmailLog(user_id=user_id,invoice_id=invoice_id,proposal_id=proposal_id,to_email=to,
                       subject=subject,email_type=email_type,status="sent" if success else "failed",
                       provider=provider,resend_id=message_id,error_msg=error)
        async with AsyncSessionLocal() as db:
            db.add(log); await db.commit()
    except Exception as e:
        logger.error(f"Email log DB error: {e}")


def _html_to_text(html:str)->str:
    import re
    text=re.sub(r'<style[^>]*>.*?</style>','',html,flags=re.DOTALL)
    return ' '.join(re.sub(r'<[^>]+>',' ',text).split())


# ─── Email builders ─────────────────────────────────────────────────────────

async def send_welcome(to,name,user_id=None):
    body=f"""<h1>Welcome, {name}! 🚀</h1>
<p>You're now set up on <span class="hl">PropelPay</span> — the smartest way to send proposals, invoice clients, and get paid faster in Africa.</p>
<div class="box"><p class="lbl">Next steps</p>
<p>1. Add your first client</p><p>2. Generate an AI proposal</p><p>3. Send an invoice with Paystack payment link</p></div>
<div class="box"><p class="lbl">Need help?</p><p>WhatsApp us: +234 704 556 0291 or email multipurposetalentedyounginven@gmail.com</p></div>"""
    return await send_email(to,f"Welcome to PropelPay, {name}! ⚡",_wrap("Welcome",body),user_id=user_id,email_type="welcome")


async def send_invoice_email(to,client_name,inv_number,total,currency,due_date,pay_link,user_name,user_id=None,invoice_id=None):
    sym={"NGN":"₦","USD":"$","GBP":"£","EUR":"€","GHS":"₵","KES":"Ksh"}.get(currency,currency)
    body=f"""<h1>Invoice from {user_name}</h1>
<p>Hello {client_name},</p>
<p>Please find your invoice details below. You can pay securely online with your card, bank transfer, or USSD.</p>
<div class="box"><div class="row"><span class="rl">Invoice</span><span class="rv">{inv_number}</span></div>
<div class="row"><span class="rl">Amount Due</span><span class="rv">{sym}{total:,.0f} {currency}</span></div>
<div class="row"><span class="rl">Due Date</span><span class="rv">{due_date}</span></div></div>
<div style="text-align:center;margin:20px 0"><a href="{pay_link}" class="btn btn-g">💳 Pay {sym}{total:,.0f} Now</a></div>
<p style="font-size:11px;text-align:center;color:#475569">Secure payment powered by Paystack · Card, Bank Transfer, USSD</p>"""
    return await send_email(to,f"Invoice {inv_number} — {sym}{total:,.0f} due {due_date}",_wrap(f"Invoice {inv_number}",body),
                            user_id=user_id,invoice_id=invoice_id,email_type="invoice")


async def send_payment_received(to,client_name,inv_number,total,currency,user_name,user_id=None,invoice_id=None):
    sym={"NGN":"₦","USD":"$","GBP":"£","EUR":"€","GHS":"₵","KES":"Ksh"}.get(currency,currency)
    body=f"""<h1>Payment Received ✅</h1>
<p>Hello {client_name},</p><p>Your payment has been received and confirmed. Thank you!</p>
<div class="box"><p class="lbl">Payment Confirmed</p><span class="amt amt-g">{sym}{total:,.0f} {currency}</span>
<div class="row"><span class="rl">Invoice</span><span class="rv">{inv_number}</span></div>
<div class="row"><span class="rl">Status</span><span class="rv" style="color:{GREEN}">PAID ✓</span></div></div>
<p>A receipt PDF is attached to this email. Thank you for your business!</p>"""
    return await send_email(to,f"Payment received — {inv_number} ✅",_wrap("Payment Received",body),
                            user_id=user_id,invoice_id=invoice_id,email_type="payment_received")


async def send_payment_reminder(to,client_name,inv_number,total,currency,due_date,pay_link,days_overdue,user_name,user_id=None,invoice_id=None):
    sym={"NGN":"₦","USD":"$","GBP":"£","EUR":"€","GHS":"₵","KES":"Ksh"}.get(currency,currency)
    overdue_msg = f"This invoice is <span style='color:#ef4444;font-weight:700'>{days_overdue} day(s) overdue.</span>" if days_overdue>0 else "This invoice is due soon."
    body=f"""<h1>Payment Reminder 🔔</h1>
<p>Hello {client_name},</p><p>A friendly reminder from <span class="hl">{user_name}</span>. {overdue_msg}</p>
<div class="box"><div class="row"><span class="rl">Invoice</span><span class="rv">{inv_number}</span></div>
<div class="row"><span class="rl">Amount Due</span><span class="rv">{sym}{total:,.0f} {currency}</span></div>
<div class="row"><span class="rl">Due Date</span><span class="rv">{due_date}</span></div></div>
<div style="text-align:center;margin:20px 0"><a href="{pay_link}" class="btn btn-p">💳 Pay Now — {sym}{total:,.0f}</a></div>"""
    return await send_email(to,f"Reminder: Invoice {inv_number} — {sym}{total:,.0f} due",_wrap("Payment Reminder",body),
                            user_id=user_id,invoice_id=invoice_id,email_type="reminder")


async def send_proposal_email(to,client_name,title,view_link,user_name,user_id=None,proposal_id=None):
    body=f"""<h1>Proposal from {user_name}</h1>
<p>Hello {client_name},</p><p>Please review the proposal below. You can view, comment on, and electronically sign it directly online.</p>
<div class="box"><p class="lbl">Proposal</p><p class="hl" style="font-size:15px;font-weight:700">{title}</p></div>
<div style="text-align:center;margin:20px 0"><a href="{view_link}" class="btn btn-p">📄 View & Sign Proposal</a></div>
<p style="font-size:11px;text-align:center;color:#475569">Powered by PropelPay · Legally binding e-signature</p>"""
    return await send_email(to,f"Proposal: {title} — from {user_name}",_wrap(f"Proposal: {title}",body),
                            user_id=user_id,proposal_id=proposal_id,email_type="proposal")
