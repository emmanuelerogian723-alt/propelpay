"""PropelPay AI Service — Proposal drafting, invoice generation, follow-up writing"""
import logging
from typing import Optional
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def _get_client():
    if settings.GROQ_API_KEY:
        from groq import Groq
        return Groq(api_key=settings.GROQ_API_KEY), "llama3-70b-8192", "groq"
    if settings.OPENROUTER_API_KEY:
        from openai import OpenAI
        return OpenAI(base_url="https://openrouter.ai/api/v1",
                      api_key=settings.OPENROUTER_API_KEY), "meta-llama/llama-3-70b-instruct", "openrouter"
    if settings.OPENAI_API_KEY:
        from openai import OpenAI
        return OpenAI(api_key=settings.OPENAI_API_KEY), "gpt-4o-mini", "openai"
    return None, None, None


def _chat(system: str, prompt: str) -> str:
    client, model, provider = _get_client()
    if not client:
        return "⚠️ No AI provider configured. Add GROQ_API_KEY to .env"
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return resp.choices[0].message.content
    except Exception as e:
        logger.error(f"AI error ({provider}): {e}")
        return f"AI generation failed: {str(e)}"


def draft_proposal(
    business_name: str,
    client_name: str,
    service_type: str,
    scope: str,
    budget: Optional[str] = None,
    tone: str = "professional"
) -> dict:
    """Generate a full professional proposal using AI."""
    system = """You are PropelPay's expert proposal writer. 
    Write winning, professional business proposals that convert clients.
    Use clear sections: Executive Summary, Scope of Work, Deliverables, Timeline, Investment, Terms.
    Be specific, persuasive, and results-focused. Format in clean Markdown."""

    prompt = f"""Write a complete business proposal:
Business: {business_name}
Client: {client_name}
Service: {service_type}
Project Scope: {scope}
Budget Range: {budget or "To be discussed"}
Tone: {tone}

Include: Executive Summary, Problem Statement, Our Solution, Scope of Work, 
Deliverables & Timeline, Investment/Pricing, Why Choose Us, Next Steps, Terms & Conditions.
Make it persuasive and professional. Use the client's name throughout."""

    content = _chat(system, prompt)

    # Generate a suggested services breakdown
    services_prompt = f"""Based on this proposal for {service_type} work worth {budget or 'unspecified budget'},
create 3-5 line item services as JSON array. Format:
[{{"name": "Service Name", "description": "Brief description", "price": 50000}}]
Use Naira (NGN) if Nigerian context, else USD. Return ONLY valid JSON array, nothing else."""
    
    services_raw = _chat("You are a pricing expert. Return only valid JSON.", services_prompt)
    
    import json, re
    try:
        match = re.search(r'\[.*\]', services_raw, re.DOTALL)
        services = json.loads(match.group()) if match else []
    except:
        services = [{"name": service_type, "description": scope[:100], "price": 0}]

    total = sum(s.get("price", 0) for s in services)

    return {"content": content, "services": services, "total": total}


def write_follow_up(
    client_name: str,
    invoice_number: str,
    amount: float,
    currency: str,
    days_overdue: int,
    business_name: str,
    attempt: int = 1
) -> str:
    """Generate a payment reminder email (escalating tone based on attempt)."""
    tones = {1: "friendly", 2: "firm but polite", 3: "urgent and serious", 4: "final notice"}
    tone = tones.get(attempt, "final notice")

    system = "You are a professional accounts receivable manager. Write effective payment reminder emails."
    prompt = f"""Write a payment reminder email:
To: {client_name}
Invoice: {invoice_number}
Amount Due: {currency} {amount:,.2f}
Days Overdue: {days_overdue}
From: {business_name}
Tone: {tone} (attempt #{attempt})

Write a complete email (Subject + Body). Be {tone}. Include invoice details, 
payment instructions, and a clear call to action. Keep it under 200 words."""

    return _chat(system, prompt)


def generate_invoice_title(services_desc: str) -> str:
    """Generate a professional invoice title from services description."""
    return _chat(
        "Generate a brief professional invoice title (max 10 words) from a services description. Return only the title.",
        f"Services: {services_desc}"
    ).strip().strip('"\'')


def ai_insights(
    total_invoiced: float,
    total_paid: float,
    overdue_count: int,
    top_client: str,
    currency: str
) -> str:
    """Generate business insights for the dashboard."""
    collection_rate = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
    system = "You are a business advisor for freelancers and agencies. Give concise, actionable insights."
    prompt = f"""Business summary:
- Total Invoiced: {currency} {total_invoiced:,.0f}
- Total Paid: {currency} {total_paid:,.0f}  
- Collection Rate: {collection_rate:.1f}%
- Overdue Invoices: {overdue_count}
- Top Client: {top_client}

Give 3 short, specific, actionable insights (bullet points). Max 100 words total."""
    return _chat(system, prompt)
