"""
PropelPay — Send. Sign. Get Paid.
FastAPI Backend v1.0
"""
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.api import auth, clients, proposals, invoices, dashboard, billing

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PropelPay API v1.0 starting...")
    await init_db()
    os.makedirs("uploads", exist_ok=True)
    yield
    logger.info("PropelPay API shutting down.")

app = FastAPI(
    title="PropelPay API",
    description="Send proposals, collect signatures, invoice clients, get paid. Automatically.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(proposals.router)
app.include_router(invoices.router)
app.include_router(dashboard.router)
app.include_router(billing.router)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "PropelPay", "version": "1.0.0"}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    """Serve landing page - checks multiple paths for flexibility."""
    search_paths = [
        "frontend/index.html",
        "/app/propelpay/frontend/index.html",
        "../frontend/index.html",
        os.path.join(os.path.dirname(__file__), "../../frontend/index.html"),
    ]
    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return HTMLResponse(f.read())
            except Exception:
                continue
    # Fallback: minimal working page
    return HTMLResponse(LANDING_HTML)

@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def serve_app():
    """Serve dashboard app."""
    search_paths = [
        "frontend/dashboard.html",
        "/app/propelpay/frontend/dashboard.html",
        "../frontend/dashboard.html",
    ]
    for path in search_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return HTMLResponse(f.read())
            except Exception:
                continue
    return HTMLResponse(LANDING_HTML)

# Embedded landing HTML (always works, even if file system differs)
LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PropelPay — Send. Sign. Get Paid.</title>
<meta name="description" content="The all-in-one platform for freelancers and agencies to send AI-powered proposals, collect e-signatures, invoice clients and get paid automatically. Built for Africa, designed for the world.">
<meta name="keywords" content="proposal software, invoice software, freelancer tools, get paid faster, paystack, e-signature, Africa">
<meta property="og:title" content="PropelPay — Send. Sign. Get Paid.">
<meta property="og:description" content="AI proposals + e-signatures + smart invoicing + auto payment chasing. One platform. Built for Africa.">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--brand:#6366f1;--brand2:#8b5cf6;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;
--bg:#0a0f1e;--card:#111827;--card2:#1e293b;--border:#1f2937;--text:#e2e8f0;--muted:#64748b;--white:#fff}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;overflow-x:hidden}
a{color:inherit;text-decoration:none}
.btn{display:inline-flex;align-items:center;gap:8px;padding:12px 24px;border-radius:10px;font-weight:700;font-size:15px;cursor:pointer;border:none;transition:.2s}
.btn-primary{background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(99,102,241,.4)}
.btn-outline{background:transparent;border:1.5px solid var(--border);color:var(--text)}
.btn-outline:hover{border-color:var(--brand);color:var(--brand)}
.btn-green{background:linear-gradient(135deg,var(--green),#059669);color:#fff}
.btn-green:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(16,185,129,.4)}
.container{max-width:1200px;margin:0 auto;padding:0 24px}
/* NAV */
nav{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(10,15,30,.9);backdrop-filter:blur(20px);border-bottom:1px solid var(--border)}
.nav-inner{display:flex;align-items:center;justify-content:space-between;padding:16px 24px;max-width:1200px;margin:0 auto}
.logo{font-size:22px;font-weight:900;background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-links{display:flex;align-items:center;gap:32px}
.nav-links a{color:var(--muted);font-size:14px;transition:.2s}
.nav-links a:hover{color:var(--text)}
.nav-cta{display:flex;gap:12px;align-items:center}
/* HERO */
.hero{min-height:100vh;display:flex;align-items:center;padding:120px 24px 80px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;
background:radial-gradient(ellipse at 60% 40%,rgba(99,102,241,.12) 0%,transparent 60%),
           radial-gradient(ellipse at 20% 80%,rgba(139,92,246,.08) 0%,transparent 50%);pointer-events:none}
.hero-content{max-width:700px}
.hero-badge{display:inline-flex;align-items:center;gap:8px;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);
border-radius:50px;padding:6px 16px;font-size:13px;color:var(--brand);margin-bottom:24px}
.hero h1{font-size:clamp(36px,6vw,72px);font-weight:900;line-height:1.05;margin-bottom:24px}
.hero h1 span{background:linear-gradient(135deg,var(--brand),var(--brand2),var(--green));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero p{font-size:19px;color:var(--muted);line-height:1.7;margin-bottom:40px;max-width:560px}
.hero-cta{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:48px}
.hero-stats{display:flex;gap:40px;flex-wrap:wrap}
.stat{display:flex;flex-direction:column}
.stat-num{font-size:28px;font-weight:800;color:var(--white)}
.stat-label{font-size:13px;color:var(--muted)}
/* FEATURES */
.section{padding:100px 0}
.section-badge{display:inline-block;background:rgba(99,102,241,.15);border:1px solid rgba(99,102,241,.3);
border-radius:50px;padding:5px 14px;font-size:12px;color:var(--brand);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px}
.section-title{font-size:clamp(28px,4vw,48px);font-weight:800;margin-bottom:16px;line-height:1.15}
.section-sub{font-size:17px;color:var(--muted);max-width:560px;line-height:1.7;margin-bottom:64px}
.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px}
.feature-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:32px;transition:.2s;position:relative;overflow:hidden}
.feature-card::before{content:'';position:absolute;inset:0;background:linear-gradient(135deg,rgba(99,102,241,.05),transparent);opacity:0;transition:.3s}
.feature-card:hover{border-color:rgba(99,102,241,.4);transform:translateY(-4px)}
.feature-card:hover::before{opacity:1}
.feature-icon{width:52px;height:52px;background:linear-gradient(135deg,var(--brand),var(--brand2));border-radius:14px;
display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:20px}
.feature-title{font-size:18px;font-weight:700;margin-bottom:8px;color:var(--white)}
.feature-desc{font-size:15px;color:var(--muted);line-height:1.7}
/* HOW IT WORKS */
.steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:0;position:relative}
.step{text-align:center;padding:32px 24px}
.step-num{width:56px;height:56px;background:linear-gradient(135deg,var(--brand),var(--brand2));border-radius:50%;
display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;color:#fff;margin:0 auto 20px}
.step-title{font-size:17px;font-weight:700;margin-bottom:8px;color:var(--white)}
.step-desc{font-size:14px;color:var(--muted);line-height:1.7}
/* PRICING */
.pricing-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:24px;margin-top:64px}
.price-card{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:36px;position:relative}
.price-card.popular{border-color:var(--brand);background:linear-gradient(135deg,rgba(99,102,241,.1),rgba(139,92,246,.05))}
.popular-badge{position:absolute;top:-14px;left:50%;transform:translateX(-50%);
background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff;font-size:12px;font-weight:700;
padding:5px 18px;border-radius:50px;white-space:nowrap}
.plan-name{font-size:14px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:8px}
.plan-price{font-size:42px;font-weight:900;color:var(--white);margin-bottom:4px}
.plan-price span{font-size:18px;font-weight:400;color:var(--muted)}
.plan-period{font-size:13px;color:var(--muted);margin-bottom:24px}
.plan-features{list-style:none;margin-bottom:32px}
.plan-features li{display:flex;align-items:center;gap:10px;padding:8px 0;font-size:14px;color:var(--text);border-bottom:1px solid rgba(255,255,255,.05)}
.plan-features li::before{content:'✓';color:var(--green);font-weight:800;flex-shrink:0}
/* TESTIMONIALS */
.testimonials{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}
.testimonial{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:28px}
.t-stars{color:var(--yellow);font-size:16px;margin-bottom:12px}
.t-text{font-size:15px;line-height:1.7;color:var(--text);margin-bottom:20px;font-style:italic}
.t-author{display:flex;align-items:center;gap:12px}
.t-avatar{width:40px;height:40px;background:linear-gradient(135deg,var(--brand),var(--brand2));border-radius:50%;
display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;font-size:16px}
.t-name{font-size:14px;font-weight:700;color:var(--white)}
.t-role{font-size:12px;color:var(--muted)}
/* FAQ */
.faq{max-width:780px;margin:64px auto 0}
.faq-item{border-bottom:1px solid var(--border);overflow:hidden}
.faq-q{width:100%;background:transparent;border:none;color:var(--text);font-size:16px;font-weight:600;
padding:20px 0;text-align:left;cursor:pointer;display:flex;justify-content:space-between;align-items:center}
.faq-q:hover{color:var(--brand)}
.faq-a{font-size:14px;color:var(--muted);line-height:1.8;padding:0 0 20px;display:none}
.faq-item.open .faq-a{display:block}
.faq-item.open .faq-icon{transform:rotate(45deg)}
.faq-icon{transition:.2s;font-size:20px;color:var(--muted)}
/* CTA SECTION */
.cta-section{background:linear-gradient(135deg,rgba(99,102,241,.15),rgba(139,92,246,.1));
border:1px solid rgba(99,102,241,.2);border-radius:24px;padding:72px 48px;text-align:center;margin:80px 0}
/* FOOTER */
footer{background:var(--card);border-top:1px solid var(--border);padding:64px 0 32px}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:48px;margin-bottom:48px}
.footer-brand .logo{font-size:20px;display:block;margin-bottom:12px}
.footer-brand p{font-size:14px;color:var(--muted);line-height:1.8;max-width:260px}
.footer-col h4{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted);margin-bottom:16px}
.footer-col a{display:block;font-size:14px;color:var(--muted);margin-bottom:10px;transition:.2s}
.footer-col a:hover{color:var(--brand)}
.footer-bottom{border-top:1px solid var(--border);padding-top:24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:gap:16px}
.footer-bottom p{font-size:13px;color:var(--muted)}
/* MODAL */
.modal-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(8px);z-index:1000;align-items:center;justify-content:center;padding:24px}
.modal-overlay.open{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:40px;width:100%;max-width:480px;position:relative}
.modal h2{font-size:22px;font-weight:800;margin-bottom:4px;color:var(--white)}
.modal p{font-size:14px;color:var(--muted);margin-bottom:28px}
.close-btn{position:absolute;top:16px;right:16px;background:transparent;border:none;color:var(--muted);font-size:22px;cursor:pointer}
.form-group{margin-bottom:18px}
.form-group label{display:block;font-size:13px;font-weight:600;color:var(--muted);margin-bottom:6px}
.form-group input,.form-group select{width:100%;background:var(--card2);border:1px solid var(--border);border-radius:10px;
padding:12px 16px;color:var(--text);font-size:14px;outline:none;transition:.2s}
.form-group input:focus,.form-group select:focus{border-color:var(--brand)}
.form-err{color:var(--red);font-size:13px;margin-top:6px;display:none}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.tabs{display:flex;border-bottom:1px solid var(--border);margin-bottom:28px}
.tab-btn{flex:1;background:transparent;border:none;color:var(--muted);font-size:15px;font-weight:600;padding:12px;cursor:pointer;transition:.2s;border-bottom:2px solid transparent}
.tab-btn.active{color:var(--brand);border-bottom-color:var(--brand)}
.spinner{display:none;width:18px;height:18px;border:2px solid rgba(255,255,255,.3);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@media(max-width:768px){
  .nav-links{display:none}.footer-grid{grid-template-columns:1fr 1fr}
  .hero h1{font-size:36px}.cta-section{padding:48px 24px}
  .form-row{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- NAV -->
<nav>
<div class="nav-inner">
  <span class="logo">⚡ PropelPay</span>
  <div class="nav-links">
    <a href="#features">Features</a>
    <a href="#how-it-works">How It Works</a>
    <a href="#pricing">Pricing</a>
    <a href="#faq">FAQ</a>
  </div>
  <div class="nav-cta">
    <button class="btn btn-outline" style="padding:9px 18px;font-size:14px" onclick="openAuth('login')">Log In</button>
    <button class="btn btn-primary" style="padding:9px 18px;font-size:14px" onclick="openAuth('register')">Start Free →</button>
  </div>
</div>
</nav>

<!-- HERO -->
<section class="hero">
<div class="container">
<div class="hero-content">
  <div class="hero-badge">🚀 Built for African freelancers &amp; agencies</div>
  <h1>Stop Chasing.<br><span>Start Getting Paid.</span></h1>
  <p>Write AI proposals in 30 seconds, collect e-signatures, send invoices and let PropelPay automatically chase your clients for payment. While you sleep.</p>
  <div class="hero-cta">
    <button class="btn btn-primary" style="padding:16px 32px;font-size:16px" onclick="openAuth('register')">Start for Free — No Credit Card ⚡</button>
    <button class="btn btn-outline" style="padding:16px 32px;font-size:16px" onclick="scrollTo('#how-it-works')">See How It Works</button>
  </div>
  <div class="hero-stats">
    <div class="stat"><span class="stat-num">$1.5T</span><span class="stat-label">Lost in unpaid invoices globally/yr</span></div>
    <div class="stat"><span class="stat-num">10hrs</span><span class="stat-label">Saved per month per user</span></div>
    <div class="stat"><span class="stat-num">43%→</span><span class="stat-label">Avg proposal close rate improvement</span></div>
  </div>
</div>
</div>
</section>

<!-- FEATURES -->
<section class="section" id="features">
<div class="container">
  <div class="section-badge">Everything You Need</div>
  <div class="section-title">One platform. Every tool you need<br>to get paid faster.</div>
  <div class="section-sub">Stop switching between 5 different tools. PropelPay combines proposals, contracts, invoicing and automated follow-ups — all powered by AI.</div>
  <div class="features-grid">
    <div class="feature-card">
      <div class="feature-icon">🤖</div>
      <div class="feature-title">AI Proposal Writer</div>
      <div class="feature-desc">Describe your project in plain English. Our AI writes a complete, professional proposal with pricing, scope, timeline and terms in under 30 seconds.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">✍️</div>
      <div class="feature-title">E-Signature Built In</div>
      <div class="feature-desc">Clients sign proposals directly from their phone or browser. No printing, no scanning. Legally binding with IP logging and timestamp.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🧾</div>
      <div class="feature-title">Smart Invoicing</div>
      <div class="feature-desc">Create professional invoices in seconds. Add line items, apply tax and discounts, set due dates. Beautiful PDF sent directly to your client.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">💳</div>
      <div class="feature-title">Paystack &amp; Bank Transfer</div>
      <div class="feature-desc">Accept Paystack payments directly on invoices. Or display your bank details for instant transfers. Money hits your account automatically.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🔁</div>
      <div class="feature-title">Auto Payment Reminders</div>
      <div class="feature-desc">AI writes escalating reminder emails for overdue invoices. From friendly to firm to urgent — sent automatically so you don't have to chase.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">📊</div>
      <div class="feature-title">Revenue Dashboard</div>
      <div class="feature-desc">See exactly what you've earned, what's pending, and what's overdue. AI insights tell you how to improve your collection rate this month.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">👥</div>
      <div class="feature-title">Client CRM</div>
      <div class="feature-desc">Keep all your client contacts organized. Full history of proposals and invoices per client. Never lose track of a deal again.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🌍</div>
      <div class="feature-title">Multi-Currency</div>
      <div class="feature-desc">Bill in NGN, USD, GBP, EUR or any currency. Serve clients in Nigeria, UK, US or anywhere in the world with the same account.</div>
    </div>
    <div class="feature-card">
      <div class="feature-icon">🔗</div>
      <div class="feature-title">Public Payment Links</div>
      <div class="feature-desc">Every invoice gets a unique shareable link. Share on WhatsApp, email or Telegram. Client pays in 2 clicks without signing up.</div>
    </div>
  </div>
</div>
</section>

<!-- HOW IT WORKS -->
<section class="section" id="how-it-works" style="background:var(--card2);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
<div class="container">
  <div style="text-align:center;margin-bottom:64px">
    <div class="section-badge">Simple Process</div>
    <div class="section-title">From project to payment in 4 steps</div>
  </div>
  <div class="steps">
    <div class="step">
      <div class="step-num">1</div>
      <div class="step-title">Add Your Client</div>
      <div class="step-desc">Save client name, email and company. Takes 30 seconds. PropelPay remembers everything.</div>
    </div>
    <div class="step">
      <div class="step-num">2</div>
      <div class="step-title">AI Writes Your Proposal</div>
      <div class="step-desc">Tell the AI your project scope. It writes a full professional proposal with pricing. You review and send.</div>
    </div>
    <div class="step">
      <div class="step-num">3</div>
      <div class="step-title">Client Signs Online</div>
      <div class="step-desc">Client receives a link, reads the proposal on their phone and signs with one tap. You get notified instantly.</div>
    </div>
    <div class="step">
      <div class="step-num">4</div>
      <div class="step-title">Get Paid Automatically</div>
      <div class="step-desc">Invoice is sent. If client delays, PropelPay sends AI-written reminders automatically until you're paid.</div>
    </div>
  </div>
</div>
</section>

<!-- PRICING -->
<section class="section" id="pricing">
<div class="container" style="text-align:center">
  <div class="section-badge">Fair Pricing</div>
  <div class="section-title">Start free. Upgrade when you're ready.</div>
  <div class="section-sub" style="margin:0 auto 0">Priced for African freelancers. No hidden fees. Cancel anytime.</div>
  <div class="pricing-grid">
    <div class="price-card">
      <div class="plan-name">Free</div>
      <div class="plan-price">₦0<span></span></div>
      <div class="plan-period">Forever free</div>
      <ul class="plan-features">
        <li>3 proposals/month</li>
        <li>5 invoices/month</li>
        <li>5 clients</li>
        <li>3 AI drafts</li>
        <li>E-signatures</li>
        <li>Paystack payments</li>
      </ul>
      <button class="btn btn-outline" style="width:100%;justify-content:center" onclick="openAuth('register')">Get Started Free</button>
    </div>
    <div class="price-card popular">
      <div class="popular-badge">⚡ Most Popular</div>
      <div class="plan-name">Solo</div>
      <div class="plan-price">₦9,900<span></span></div>
      <div class="plan-period">per month · ~$15 USD</div>
      <ul class="plan-features">
        <li>50 proposals/month</li>
        <li>100 invoices/month</li>
        <li>50 clients</li>
        <li>50 AI drafts</li>
        <li>Auto payment reminders</li>
        <li>Priority email support</li>
      </ul>
      <button class="btn btn-primary" style="width:100%;justify-content:center" onclick="openAuth('register')">Start Solo Plan →</button>
    </div>
    <div class="price-card">
      <div class="plan-name">Agency</div>
      <div class="plan-price">₦24,900<span></span></div>
      <div class="plan-period">per month · ~$29 USD</div>
      <ul class="plan-features">
        <li>Unlimited proposals</li>
        <li>Unlimited invoices</li>
        <li>Unlimited clients</li>
        <li>Unlimited AI drafts</li>
        <li>White-label PDFs</li>
        <li>API access</li>
        <li>Priority support</li>
      </ul>
      <button class="btn btn-outline" style="width:100%;justify-content:center" onclick="openAuth('register')">Start Agency Plan</button>
    </div>
    <div class="price-card">
      <div class="plan-name">Enterprise</div>
      <div class="plan-price">₦79,900<span></span></div>
      <div class="plan-period">per month · ~$79 USD</div>
      <ul class="plan-features">
        <li>Everything in Agency</li>
        <li>Custom branding</li>
        <li>Dedicated support</li>
        <li>Custom integrations</li>
        <li>SLA guarantee</li>
        <li>Team accounts</li>
      </ul>
      <button class="btn btn-outline" style="width:100%;justify-content:center" onclick="openAuth('register')">Contact Sales</button>
    </div>
  </div>
</div>
</section>

<!-- TESTIMONIALS -->
<section class="section" style="background:var(--card2);border-top:1px solid var(--border);border-bottom:1px solid var(--border)">
<div class="container">
  <div style="text-align:center;margin-bottom:64px">
    <div class="section-badge">Social Proof</div>
    <div class="section-title">Freelancers are already getting paid faster</div>
  </div>
  <div class="testimonials">
    <div class="testimonial">
      <div class="t-stars">★★★★★</div>
      <div class="t-text">"I used to spend 3 hours writing proposals. Now PropelPay AI does it in 30 seconds and my close rate went from 30% to 65%. This tool literally makes me money."</div>
      <div class="t-author"><div class="t-avatar">A</div><div><div class="t-name">Adaeze Okafor</div><div class="t-role">UI/UX Designer, Lagos</div></div></div>
    </div>
    <div class="testimonial">
      <div class="t-stars">★★★★★</div>
      <div class="t-text">"I had ₦840,000 sitting in overdue invoices. PropelPay's automatic reminders recovered ₦620,000 in 2 weeks without me sending a single message myself."</div>
      <div class="t-author"><div class="t-avatar">K</div><div><div class="t-name">Kwame Asante</div><div class="t-role">Marketing Agency Owner, Accra</div></div></div>
    </div>
    <div class="testimonial">
      <div class="t-stars">★★★★★</div>
      <div class="t-text">"As a developer working with UK clients, PropelPay lets me invoice in GBP and accept Paystack in Nigeria. The e-signature feature makes contracts seamless."</div>
      <div class="t-author"><div class="t-avatar">T</div><div><div class="t-name">Tunde Adeleke</div><div class="t-role">Fullstack Developer, Abuja</div></div></div>
    </div>
  </div>
</div>
</section>

<!-- FAQ -->
<section class="section" id="faq">
<div class="container" style="text-align:center">
  <div class="section-badge">FAQ</div>
  <div class="section-title">Frequently Asked Questions</div>
  <div class="faq">
    <div class="faq-item">
      <button class="faq-q" onclick="toggleFaq(this)">Is PropelPay really free to start? <span class="faq-icon">+</span></button>
      <div class="faq-a">Yes — completely free, no credit card needed. You get 3 proposals, 5 invoices, 5 clients and 3 AI drafts per month. Upgrade only when you need more.</div>
    </div>
    <div class="faq-item">
      <button class="faq-q" onclick="toggleFaq(this)">How does the AI proposal writer work? <span class="faq-icon">+</span></button>
      <div class="faq-a">You describe your service, scope and client name. Our AI (powered by Groq/Llama) writes a complete professional proposal with executive summary, scope of work, deliverables, timeline, pricing and terms. You can edit anything before sending.</div>
    </div>
    <div class="faq-item">
      <button class="faq-q" onclick="toggleFaq(this)">Are e-signatures legally binding? <span class="faq-icon">+</span></button>
      <div class="faq-a">Yes. PropelPay captures the signer's name, email, IP address, timestamp and browser fingerprint. This creates an audit trail that is legally binding in Nigeria and most countries under electronic signature laws.</div>
    </div>
    <div class="faq-item">
      <button class="faq-q" onclick="toggleFaq(this)">How does automatic payment chasing work? <span class="faq-icon">+</span></button>
      <div class="faq-a">When an invoice is overdue, PropelPay sends AI-written reminder emails to your client. The tone escalates from friendly to firm to urgent the longer it's overdue. You can also manually trigger reminders anytime from your dashboard.</div>
    </div>
    <div class="faq-item">
      <button class="faq-q" onclick="toggleFaq(this)">Can my clients pay without signing up? <span class="faq-icon">+</span></button>
      <div class="faq-a">Yes. Every invoice gets a unique public link. Your client opens it, sees the invoice and pays directly via Paystack — no account needed. You can also share the link on WhatsApp or any messaging app.</div>
    </div>
    <div class="faq-item">
      <button class="faq-q" onclick="toggleFaq(this)">What currencies are supported? <span class="faq-icon">+</span></button>
      <div class="faq-a">You can invoice in any currency — NGN, USD, GBP, EUR, GHS, KES and more. Paystack payments work in NGN, USD, GBP and EUR. For other currencies, bank transfer details are displayed automatically.</div>
    </div>
  </div>
</div>
</section>

<!-- FINAL CTA -->
<section class="section">
<div class="container">
  <div class="cta-section">
    <div style="font-size:48px;margin-bottom:16px">⚡</div>
    <h2 style="font-size:42px;font-weight:900;margin-bottom:16px;color:var(--white)">Stop losing money to late payments.</h2>
    <p style="font-size:18px;color:var(--muted);max-width:480px;margin:0 auto 40px;line-height:1.7">Join thousands of freelancers and agencies who send faster proposals and collect payments automatically with PropelPay.</p>
    <button class="btn btn-primary" style="padding:18px 40px;font-size:17px" onclick="openAuth('register')">Start for Free — Takes 60 Seconds →</button>
    <p style="margin-top:16px;font-size:13px;color:var(--muted)">No credit card · Free forever plan · Setup in 60 seconds</p>
  </div>
</div>
</section>

<!-- FOOTER -->
<footer>
<div class="container">
  <div class="footer-grid">
    <div class="footer-brand">
      <span class="logo">⚡ PropelPay</span>
      <p>The all-in-one platform for freelancers and agencies to send proposals, collect signatures and get paid faster.</p>
    </div>
    <div class="footer-col">
      <h4>Product</h4>
      <a href="#features">Features</a>
      <a href="#pricing">Pricing</a>
      <a href="#how-it-works">How It Works</a>
      <a href="/docs">API Docs</a>
    </div>
    <div class="footer-col">
      <h4>Use Cases</h4>
      <a href="#">Freelancers</a>
      <a href="#">Agencies</a>
      <a href="#">Consultants</a>
      <a href="#">Small Business</a>
    </div>
    <div class="footer-col">
      <h4>Company</h4>
      <a href="#">About</a>
      <a href="#">Privacy Policy</a>
      <a href="#">Terms of Service</a>
      <a href="#">Contact</a>
    </div>
  </div>
  <div class="footer-bottom">
    <p>© 2026 PropelPay. Built with ❤️ for African creators.</p>
    <p>Powered by Paystack · AI by Groq</p>
  </div>
</div>
</footer>

<!-- AUTH MODAL -->
<div class="modal-overlay" id="authModal">
<div class="modal">
  <button class="close-btn" onclick="closeAuth()">×</button>
  <div class="tabs">
    <button class="tab-btn active" id="loginTab" onclick="switchTab('login')">Log In</button>
    <button class="tab-btn" id="registerTab" onclick="switchTab('register')">Sign Up Free</button>
  </div>
  <!-- LOGIN FORM -->
  <div id="loginForm">
    <h2>Welcome back 👋</h2>
    <p>Log in to your PropelPay account</p>
    <div class="form-group"><label>Email</label><input type="email" id="loginEmail" placeholder="you@example.com"></div>
    <div class="form-group"><label>Password</label><input type="password" id="loginPassword" placeholder="••••••••"></div>
    <div class="form-err" id="loginErr"></div>
    <button class="btn btn-primary" style="width:100%;justify-content:center;margin-top:8px" onclick="doLogin()" id="loginBtn">
      <span class="spinner" id="loginSpinner"></span>Log In →
    </button>
  </div>
  <!-- REGISTER FORM -->
  <div id="registerForm" style="display:none">
    <h2>Create your account 🚀</h2>
    <p>Free forever. No credit card needed.</p>
    <div class="form-row">
      <div class="form-group"><label>Your Name</label><input type="text" id="regName" placeholder="Tunde Adeleke"></div>
      <div class="form-group"><label>Business Name</label><input type="text" id="regBiz" placeholder="TechStudio NG"></div>
    </div>
    <div class="form-group"><label>Email</label><input type="email" id="regEmail" placeholder="you@example.com"></div>
    <div class="form-row">
      <div class="form-group"><label>Password</label><input type="password" id="regPass" placeholder="Min 8 characters"></div>
      <div class="form-group"><label>Currency</label>
        <select id="regCurrency"><option value="NGN">NGN — Nigerian Naira</option><option value="USD">USD — US Dollar</option><option value="GBP">GBP — British Pound</option><option value="EUR">EUR — Euro</option><option value="GHS">GHS — Ghanaian Cedi</option><option value="KES">KES — Kenyan Shilling</option></select>
      </div>
    </div>
    <div class="form-err" id="regErr"></div>
    <button class="btn btn-green" style="width:100%;justify-content:center;margin-top:8px" onclick="doRegister()" id="regBtn">
      <span class="spinner" id="regSpinner"></span>Create Free Account →
    </button>
    <p style="font-size:12px;color:var(--muted);text-align:center;margin-top:12px">By signing up you agree to our Terms of Service and Privacy Policy</p>
  </div>
</div>
</div>

<script>
const API = window.location.origin;

function openAuth(tab){ document.getElementById('authModal').classList.add('open'); switchTab(tab) }
function closeAuth(){ document.getElementById('authModal').classList.remove('open') }
function switchTab(t){
  document.getElementById('loginForm').style.display = t==='login'?'block':'none';
  document.getElementById('registerForm').style.display = t==='register'?'block':'none';
  document.getElementById('loginTab').classList.toggle('active',t==='login');
  document.getElementById('registerTab').classList.toggle('active',t==='register');
}
function scrollTo(sel){ document.querySelector(sel)?.scrollIntoView({behavior:'smooth'}) }
function toggleFaq(btn){ btn.closest('.faq-item').classList.toggle('open') }

function showErr(id,msg){ const e=document.getElementById(id); e.textContent=msg; e.style.display='block' }
function hideErr(id){ document.getElementById(id).style.display='none' }
function setLoading(btnId, spinnerId, loading){
  const btn=document.getElementById(btnId), sp=document.getElementById(spinnerId);
  btn.disabled=loading; sp.style.display=loading?'inline-block':'none';
}

async function doLogin(){
  hideErr('loginErr');
  const email=document.getElementById('loginEmail').value.trim();
  const pass=document.getElementById('loginPassword').value;
  if(!email||!pass){ showErr('loginErr','Please fill all fields'); return; }
  setLoading('loginBtn','loginSpinner',true);
  try{
    const r=await fetch(`${API}/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password:pass})});
    const d=await r.json();
    if(!r.ok){ showErr('loginErr',d.detail||'Login failed'); return; }
    localStorage.setItem('pp_token',d.token);
    localStorage.setItem('pp_user',JSON.stringify(d.user));
    window.location.href='/dashboard';
  }catch(e){ showErr('loginErr','Network error. Please try again.'); }
  finally{ setLoading('loginBtn','loginSpinner',false); }
}

async function doRegister(){
  hideErr('regErr');
  const name=document.getElementById('regName').value.trim();
  const biz=document.getElementById('regBiz').value.trim();
  const email=document.getElementById('regEmail').value.trim();
  const pass=document.getElementById('regPass').value;
  const currency=document.getElementById('regCurrency').value;
  if(!name||!email||!pass){ showErr('regErr','Please fill all required fields'); return; }
  if(pass.length<8){ showErr('regErr','Password must be at least 8 characters'); return; }
  setLoading('regBtn','regSpinner',true);
  try{
    const r=await fetch(`${API}/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({name,email,password:pass,business_name:biz||name,currency})});
    const d=await r.json();
    if(!r.ok){ showErr('regErr',d.detail||'Registration failed'); return; }
    localStorage.setItem('pp_token',d.token);
    localStorage.setItem('pp_user',JSON.stringify(d.user));
    window.location.href='/dashboard';
  }catch(e){ showErr('regErr','Network error. Please try again.'); }
  finally{ setLoading('regBtn','regSpinner',false); }
}

// Close modal on overlay click
document.getElementById('authModal').addEventListener('click',function(e){ if(e.target===this)closeAuth(); });
// Enter key support
document.addEventListener('keydown',e=>{ if(e.key==='Escape')closeAuth(); });
// Check if already logged in
if(localStorage.getItem('pp_token') && window.location.pathname==='/'){
  // Don't auto-redirect on landing page
}
</script>
</body>
</html>
"""
