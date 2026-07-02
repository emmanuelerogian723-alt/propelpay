"""PropelPay AI Chatbot — strict, PropelPay-only assistant with lead capture & WhatsApp escalation.

Design notes:
- The widget UI has ALWAYS-VISIBLE "Get Started Free" and "Talk to a Human" buttons —
  those two critical actions never depend on the LLM behaving correctly.
- Off-topic requests are rejected with a fixed, deterministic message (no API call needed)
  before ever reaching the model, as a hard guarantee of strictness.
- Urgent/frustrated messages are detected with a deterministic keyword match (not left to
  the model to decide), so a WhatsApp handoff is always offered when it matters.
"""
import re, logging, urllib.parse
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db
from app.services.email import send_email, _wrap
from app.models.chat_lead import ChatLead

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chatbot", tags=["chatbot"])

WHATSAPP_NUMBER = "2347045560291"
FOUNDER_EMAIL = "multipurposetalentedyounginven@gmail.com"

SYSTEM_PROMPT = """You are "Propel", the official AI assistant embedded on the PropelPay website.

PropelPay is a SaaS platform (by MUTYINT, founded by Emmanuel Ene Rejoice) that helps African \
freelancers and agencies stop chasing clients and get paid faster. Core features you can explain:
- AI-written proposals with e-signatures
- Invoicing with Paystack payment links (card, bank transfer, USSD, mobile money)
- Automated WhatsApp payment reminders
- Recurring/retainer billing
- A project tracker (progress %, photo updates, and converting a project into an invoice)
- Multi-currency support: NGN, GHS, KES, ZAR, USD, GBP, EUR
- Pricing: Free (3 invoices/mo, 3 AI proposals, 5 clients, forever free, no card needed),
  Solo ₦9,900/mo (~$6 — 100 invoices, 50 proposals, 50 clients, recurring billing, WhatsApp
  reminders), Agency ₦24,900/mo (~$15 — unlimited everything + API access + white-label PDF).
- Support: WhatsApp +234 704 556 0291, email multipurposetalentedyounginven@gmail.com

STRICT RULES — follow all of these:
1. ONLY answer questions about PropelPay: its features, pricing, how to use it, signing up,
   billing, or troubleshooting. Do not answer general knowledge, coding help, other companies,
   or anything unrelated — politely decline and point them to WhatsApp support instead.
2. Never invent features, prices, or policies that are not listed above. If unsure, say you're
   not certain and suggest WhatsApping the team.
3. Keep replies short and conversational — 2-4 sentences max, like a helpful human, not an essay.
4. When someone shows buying intent ("how do I start", "sign me up", "I want to try it"), tell
   them to tap the "Get Started Free" button above the chat to get their signup link instantly.
5. Never ask for payment card details, passwords, or sensitive info in the chat.
"""

URGENT_PATTERNS = [
    r"\bnot working\b", r"\bbroken\b", r"\bbug\b", r"\berror\b", r"\burgent\b",
    r"\brefund\b", r"charged twice", r"double charg", r"\bfraud\b", r"\bscam\b",
    r"can'?t log ?in", r"cannot log ?in", r"locked out", r"payment failed",
    r"\bcomplaint\b", r"\bangry\b", r"\blawyer\b", r"legal action", r"\bhuman\b",
    r"real person", r"\bagent\b", r"support team", r"\bemergency\b", r"\bhacked\b",
    r"\bstolen\b", r"unauthorized", r"speak to (someone|a person|support)",
    r"\bcancel my (account|subscription)\b", r"\bdispute\b",
]

OFFTOPIC_HINTS = [
    r"\bweather\b", r"\brecipe\b", r"write (me )?a poem", r"write (me )?code for",
    r"who won", r"translate this", r"\bhomework\b", r"essay for me", r"\bjoke\b",
    r"stock price", r"crypto price", r"\belection\b", r"\bpolitic", r"\bmovie\b",
    r"song lyrics", r"who is the president", r"solve this math",
]

FIXED_REFUSAL = (
    "I'm only able to help with PropelPay questions — proposals, invoicing, payments, "
    "WhatsApp reminders, pricing, or using your dashboard.\n\n"
    "For anything else, our team is happy to help on WhatsApp: "
    f"https://wa.me/{WHATSAPP_NUMBER}"
)


def _is_urgent(msg: str) -> bool:
    m = msg.lower()
    return any(re.search(p, m) for p in URGENT_PATTERNS)


def _is_offtopic(msg: str) -> bool:
    m = msg.lower()
    return any(re.search(p, m) for p in OFFTOPIC_HINTS)


def _wa_link(prefill: str) -> str:
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={urllib.parse.quote(prefill)}"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    reply: str
    escalate: bool = False
    whatsapp_link: Optional[str] = None


class LeadRequest(BaseModel):
    name: str
    email: EmailStr
    whatsapp: str
    note: Optional[str] = None


@router.post("/message", response_model=ChatResponse)
async def chatbot_message(body: ChatRequest):
    msg = (body.message or "").strip()
    if not msg:
        raise HTTPException(400, "Empty message")
    if len(msg) > 800:
        msg = msg[:800]

    urgent = _is_urgent(msg)

    if _is_offtopic(msg) and not urgent:
        return ChatResponse(reply=FIXED_REFUSAL, escalate=False)

    from app.services.ai import _get_client
    try:
        client, model, provider = _get_client()
    except Exception as e:
        logger.error(f"AI client init crashed: {e}")
        client, model, provider = None, None, None
    if not client:
        return ChatResponse(
            reply="Our AI assistant is warming up 🙏 Meanwhile, tap 'Talk to a Human' and our team will help right away.",
            escalate=True,
            whatsapp_link=_wa_link("Hi, I have a question about PropelPay"),
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in (body.history or [])[-8:]:
        if h.role in ("user", "assistant"):
            messages.append({"role": h.role, "content": h.content[:800]})
    messages.append({"role": "user", "content": msg})

    reply = None
    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=0.5, max_tokens=350,
        )
        reply = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Chatbot AI error: {e}")
        reply = "Sorry, I'm having a small hiccup right now 🙏 Please try again in a moment, or tap 'Talk to a Human' below."
        urgent = True

    wa_link = _wa_link(f"Hi, I need help with PropelPay. My question: {msg[:200]}") if urgent else None
    return ChatResponse(reply=reply, escalate=urgent, whatsapp_link=wa_link)


@router.post("/lead")
async def chatbot_lead(body: LeadRequest, db: AsyncSession = Depends(get_db)):
    lead = ChatLead(name=body.name.strip(), email=str(body.email), whatsapp=body.whatsapp.strip(), note=body.note)
    db.add(lead)
    await db.commit()

    html = _wrap("New Chatbot Lead", f"""
    <h1>🎯 New lead from the AI chat widget</h1>
    <div class="box">
      <p class="lbl">Name</p><p class="hl">{body.name}</p>
      <p class="lbl">Email</p><p class="hl">{body.email}</p>
      <p class="lbl">WhatsApp</p><p class="hl">{body.whatsapp}</p>
    </div>
    <p>Captured at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC via the website chatbot. Consider following up personally.</p>
    """)
    try:
        await send_email(FOUNDER_EMAIL, f"🎯 New PropelPay Lead: {body.name}", html, email_type="chatbot_lead")
    except Exception as e:
        logger.error(f"Lead notification email failed: {e}")

    first_name = body.name.strip().split(" ")[0] if body.name.strip() else "there"
    return {
        "success": True,
        "signup_url": "/register",
        "message": f"Thanks {first_name}! Here's your free signup link 👇",
    }
