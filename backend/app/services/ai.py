"""PropelPay AI Service — Powered by Groq llama-3.3-70b-versatile"""
import logging
from typing import Optional
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# Best free Groq model as of 2026
GROQ_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


def _get_client():
    if settings.GROQ_API_KEY:
        try:
            from groq import Groq
            return Groq(api_key=settings.GROQ_API_KEY), GROQ_MODEL, "groq"
        except Exception as e:
            logger.error(f"Groq init failed: {e}")
    if settings.OPENROUTER_API_KEY:
        from openai import OpenAI
        return OpenAI(base_url="https://openrouter.ai/api/v1",
                      api_key=settings.OPENROUTER_API_KEY), "meta-llama/llama-3.3-70b-instruct", "openrouter"
    if settings.OPENAI_API_KEY:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o-mini", "openai"
    return None, None, None


def _chat(system: str, prompt: str, max_tokens: int = 1500) -> str:
    client, model, provider = _get_client()
    if not client:
        return "⚠️ No AI provider configured. Add GROQ_API_KEY in your environment variables."
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"AI error ({provider}/{model}): {e}")
        # Try fallback model if primary fails
        if provider == "groq" and model != FALLBACK_MODEL:
            try:
                resp = client.chat.completions.create(
                    model=FALLBACK_MODEL,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content
            except Exception as e2:
                logger.error(f"Fallback model also failed: {e2}")
        return f"AI generation failed: {str(e)}"


def draft_proposal(business_name, client_name, service_type, scope,
                   budget=None, tone="professional") -> dict:
    system = """You are PropelPay's expert proposal writer for African freelancers and agencies.
Write winning, professional business proposals. Use clear sections.
Be specific, persuasive, and results-focused. Format in clean Markdown."""

    prompt = f"""Write a complete business proposal:
Business: {business_name}
Client: {client_name}
Service: {service_type}
Scope: {scope}
Budget: {budget or 'To be discussed'}
Tone: {tone}

Include: Executive Summary, Problem Statement, Our Solution, Scope of Work,
Deliverables & Timeline, Investment/Pricing, Why Choose Us, Next Steps, Terms.
Be persuasive and specific. Use client name throughout."""

    content = _chat(system, prompt, max_tokens=2000)

    services_prompt = f"""For {service_type} work ({budget or 'unspecified budget'}),
create 3-5 line items as JSON array:
[{{"name": "Service", "description": "Brief desc", "price": 50000}}]
Use NGN if Nigerian context. Return ONLY valid JSON array."""

    services_raw = _chat("Return only valid JSON. No explanation.", services_prompt, max_tokens=400)

    import json, re
    try:
        match = re.search(r'\[.*?\]', services_raw, re.DOTALL)
        services = json.loads(match.group()) if match else []
    except:
        services = [{"name": service_type, "description": scope[:100], "price": 0}]

    total = sum(s.get("price", 0) for s in services)
    return {"content": content, "services": services, "total": total}


def write_follow_up(client_name, invoice_number, amount, currency, days_overdue,
                    business_name, attempt=1) -> str:
    tones = {1: "friendly", 2: "firm but polite", 3: "urgent and serious", 4: "final notice"}
    tone = tones.get(attempt, "final notice")
    system = "You are a professional accounts receivable manager. Write effective, concise payment reminders."
    prompt = f"""Write a payment reminder email:
To: {client_name}
Invoice: {invoice_number}
Amount: {currency} {amount:,.2f}
Days Overdue: {days_overdue}
From: {business_name}
Tone: {tone} (attempt #{attempt})
Include Subject line + Body. Keep under 150 words."""
    return _chat(system, prompt, max_tokens=300)


def generate_invoice_title(services_desc: str) -> str:
    return _chat(
        "Generate a brief professional invoice title (max 8 words). Return ONLY the title, nothing else.",
        f"Services: {services_desc}", max_tokens=50
    ).strip().strip('"\'')


def ai_insights(total_invoiced, total_paid, overdue_count, top_client, currency) -> str:
    collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
    system = "You are a business advisor for freelancers. Give concise, actionable insights in 3 bullet points."
    prompt = f"""Business stats:
- Invoiced: {currency} {total_invoiced:,.0f}
- Paid: {currency} {total_paid:,.0f} ({collection_rate:.0f}% collection rate)
- Overdue: {overdue_count} invoices
- Top client: {top_client}

Give 3 specific, actionable bullet points. Max 80 words. Be direct."""
    return _chat(system, prompt, max_tokens=200)
