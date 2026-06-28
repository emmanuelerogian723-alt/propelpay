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
from app.database import init_db
from app.api import auth, clients, proposals, invoices, dashboard, billing

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PropelPay starting...")
    await init_db()
    os.makedirs("uploads", exist_ok=True)
    yield

app = FastAPI(
    title="PropelPay API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(proposals.router)
app.include_router(invoices.router)
app.include_router(dashboard.router)
app.include_router(billing.router)

# ── HTML Pages ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "service": "PropelPay", "version": "1.0.0"}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root():
    return HTMLResponse(LANDING_HTML)

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
async def serve_app():
    return HTMLResponse(DASHBOARD_HTML)

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def serve_login():
    return HTMLResponse(LANDING_HTML)

@app.get("/register", response_class=HTMLResponse, include_in_schema=False)
async def serve_register():
    return HTMLResponse(LANDING_HTML)

# ── Embedded HTML ────────────────────────────────────────

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

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PropelPay Dashboard</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚡</text></svg>">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--brand:#6366f1;--brand2:#8b5cf6;--green:#10b981;--red:#ef4444;--yellow:#f59e0b;
--bg:#0a0f1e;--sidebar:#0d1117;--card:#111827;--card2:#1e293b;--border:#1f2937;
--text:#e2e8f0;--muted:#64748b;--white:#fff}
body{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;display:flex;height:100vh;overflow:hidden}
.sidebar{width:240px;background:var(--sidebar);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0}
.sidebar-logo{padding:20px;border-bottom:1px solid var(--border)}
.logo{font-size:18px;font-weight:900;background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.nav-items{padding:12px;flex:1}
.nav-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-radius:8px;font-size:14px;color:var(--muted);cursor:pointer;transition:.15s;margin-bottom:2px}
.nav-item:hover{background:rgba(99,102,241,.1);color:var(--text)}
.nav-item.active{background:rgba(99,102,241,.15);color:var(--brand);font-weight:600}
.nav-icon{font-size:16px;width:20px;text-align:center}
.sidebar-user{padding:16px;border-top:1px solid var(--border)}
.user-info{display:flex;align-items:center;gap:10px}
.avatar{width:36px;height:36px;background:linear-gradient(135deg,var(--brand),var(--brand2));border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0}
.user-name{font-size:13px;font-weight:600;color:var(--white)}
.user-plan{font-size:11px;color:var(--muted)}
.main{flex:1;overflow-y:auto;display:flex;flex-direction:column}
.topbar{background:var(--sidebar);border-bottom:1px solid var(--border);padding:16px 28px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.topbar h1{font-size:20px;font-weight:700}
.topbar-actions{display:flex;gap:10px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 18px;border-radius:8px;font-weight:600;font-size:13px;cursor:pointer;border:none;transition:.15s}
.btn-primary{background:linear-gradient(135deg,var(--brand),var(--brand2));color:#fff}
.btn-primary:hover{opacity:.9}
.btn-outline{background:transparent;border:1px solid var(--border);color:var(--text)}
.btn-outline:hover{border-color:var(--brand);color:var(--brand)}
.btn-green{background:linear-gradient(135deg,var(--green),#059669);color:#fff}
.btn-red{background:var(--red);color:#fff}
.btn-sm{padding:6px 12px;font-size:12px}
.content{padding:28px;flex:1}
.page{display:none}
.page.active{display:block}
/* Stats */
.stats-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px}
.stat-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin-bottom:8px}
.stat-value{font-size:26px;font-weight:800;color:var(--white)}
.stat-change{font-size:12px;margin-top:4px}
.green{color:var(--green)}.red{color:var(--red)}.yellow{color:var(--yellow)}
/* Table */
.table-card{background:var(--card);border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:20px}
.table-header{padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.table-header h3{font-size:15px;font-weight:700}
table{width:100%;border-collapse:collapse}
th{padding:12px 20px;text-align:left;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;background:var(--card2);border-bottom:1px solid var(--border)}
td{padding:14px 20px;font-size:13px;border-bottom:1px solid rgba(255,255,255,.04)}
tr:last-child td{border-bottom:none}
tr:hover td{background:rgba(255,255,255,.02)}
.badge{display:inline-flex;align-items:center;padding:3px 10px;border-radius:50px;font-size:11px;font-weight:600}
.badge-draft{background:rgba(100,116,139,.2);color:#94a3b8}
.badge-sent{background:rgba(99,102,241,.2);color:#818cf8}
.badge-viewed{background:rgba(245,158,11,.15);color:#fbbf24}
.badge-paid{background:rgba(16,185,129,.15);color:#34d399}
.badge-overdue{background:rgba(239,68,68,.15);color:#f87171}
.badge-accepted{background:rgba(16,185,129,.15);color:#34d399}
.badge-declined{background:rgba(239,68,68,.15);color:#f87171}
/* Modal */
.overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(8px);z-index:1000;align-items:center;justify-content:center;padding:20px}
.overlay.open{display:flex}
.modal{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:28px;width:100%;max-width:560px;max-height:90vh;overflow-y:auto}
.modal h2{font-size:18px;font-weight:700;margin-bottom:16px;color:var(--white)}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin-bottom:5px}
.form-group input,.form-group select,.form-group textarea{width:100%;background:var(--card2);border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-size:13px;outline:none;transition:.15s}
.form-group input:focus,.form-group select:focus,.form-group textarea:focus{border-color:var(--brand)}
.form-group textarea{min-height:80px;resize:vertical;font-family:inherit}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.form-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:20px}
.item-row{display:grid;grid-template-columns:3fr 1fr 1.5fr auto;gap:8px;align-items:center;margin-bottom:8px}
.item-row input{background:var(--card2);border:1px solid var(--border);border-radius:6px;padding:8px 10px;color:var(--text);font-size:13px;outline:none}
.remove-btn{background:rgba(239,68,68,.15);color:var(--red);border:none;border-radius:6px;padding:8px 10px;cursor:pointer;font-size:14px}
.ai-result{background:var(--card2);border:1px solid rgba(99,102,241,.3);border-radius:10px;padding:16px;margin:12px 0;font-size:13px;line-height:1.7;color:var(--text);max-height:200px;overflow-y:auto}
.loading{text-align:center;padding:40px;color:var(--muted)}
.empty{text-align:center;padding:60px 20px;color:var(--muted)}
.empty-icon{font-size:40px;margin-bottom:12px}
/* Chart */
.chart-container{height:160px;display:flex;align-items:flex-end;gap:8px;padding:0 4px}
.bar-wrap{flex:1;display:flex;flex-direction:column;align-items:center;gap:4px}
.bar{background:linear-gradient(180deg,var(--brand),var(--brand2));border-radius:4px 4px 0 0;min-height:4px;transition:.5s}
.bar-label{font-size:10px;color:var(--muted)}
/* Alert */
.alert{padding:12px 16px;border-radius:8px;font-size:13px;margin-bottom:16px}
.alert-success{background:rgba(16,185,129,.1);border:1px solid rgba(16,185,129,.3);color:var(--green)}
.alert-error{background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);color:var(--red)}
.alert-info{background:rgba(99,102,241,.1);border:1px solid rgba(99,102,241,.3);color:#818cf8}
/* Insights */
.insight-card{background:linear-gradient(135deg,rgba(99,102,241,.1),rgba(139,92,246,.05));border:1px solid rgba(99,102,241,.2);border-radius:12px;padding:20px;margin-bottom:20px}
@media(max-width:768px){
  .sidebar{display:none}.stats-grid{grid-template-columns:1fr 1fr}
  .item-row{grid-template-columns:1fr;}.form-row{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- SIDEBAR -->
<div class="sidebar">
  <div class="sidebar-logo"><span class="logo">⚡ PropelPay</span></div>
  <div class="nav-items">
    <div class="nav-item active" onclick="showPage('overview')"><span class="nav-icon">📊</span>Overview</div>
    <div class="nav-item" onclick="showPage('proposals')"><span class="nav-icon">📄</span>Proposals</div>
    <div class="nav-item" onclick="showPage('invoices')"><span class="nav-icon">🧾</span>Invoices</div>
    <div class="nav-item" onclick="showPage('clients')"><span class="nav-icon">👥</span>Clients</div>
    <div class="nav-item" onclick="showPage('settings')"><span class="nav-icon">⚙️</span>Settings</div>
  </div>
  <div class="sidebar-user">
    <div class="user-info">
      <div class="avatar" id="sideAvatar">U</div>
      <div><div class="user-name" id="sideUsername">Loading…</div><div class="user-plan" id="sidePlan">Free Plan</div></div>
    </div>
  </div>
</div>

<!-- MAIN -->
<div class="main">
<div class="topbar">
  <h1 id="pageTitle">Overview</h1>
  <div class="topbar-actions">
    <button class="btn btn-primary" id="topbarAction" onclick="topbarActionFn()">+ New Invoice</button>
    <button class="btn btn-outline btn-sm" onclick="logout()">Log Out</button>
  </div>
</div>
<div class="content">

<!-- OVERVIEW PAGE -->
<div class="page active" id="page-overview">
  <div id="alertBox"></div>
  <div class="stats-grid" id="statsGrid">
    <div class="stat-card"><div class="stat-label">Total Invoiced</div><div class="stat-value" id="statInvoiced">—</div></div>
    <div class="stat-card"><div class="stat-label">Total Paid</div><div class="stat-value green" id="statPaid">—</div></div>
    <div class="stat-card"><div class="stat-label">Pending</div><div class="stat-value yellow" id="statPending">—</div></div>
    <div class="stat-card"><div class="stat-label">Overdue</div><div class="stat-value red" id="statOverdue">—</div></div>
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px">
    <div class="stat-card" style="grid-column:1">
      <div class="stat-label">Monthly Revenue</div>
      <div class="chart-container" id="revenueChart"><div class="loading">Loading chart…</div></div>
    </div>
    <div class="insight-card" style="grid-column:2">
      <div style="font-size:13px;font-weight:700;color:var(--white);margin-bottom:8px">🤖 AI Insights</div>
      <div id="aiInsights" style="font-size:13px;color:var(--muted);line-height:1.7">Loading insights…</div>
    </div>
  </div>
  <div class="table-card">
    <div class="table-header"><h3>Recent Activity</h3></div>
    <table><thead><tr><th>Type</th><th>Title</th><th>Amount</th><th>Status</th><th>Date</th></tr></thead>
    <tbody id="recentTbody"><tr><td colspan="5" class="loading">Loading…</td></tr></tbody></table>
  </div>
</div>

<!-- PROPOSALS PAGE -->
<div class="page" id="page-proposals">
  <div style="display:flex;gap:10px;margin-bottom:20px">
    <button class="btn btn-primary" onclick="openNewProposal()">🤖 AI Proposal</button>
    <button class="btn btn-outline" onclick="openNewProposal(false)">+ Manual Proposal</button>
  </div>
  <div class="table-card">
    <div class="table-header"><h3>Proposals</h3><span id="propCount" style="font-size:12px;color:var(--muted)"></span></div>
    <table><thead><tr><th>Title</th><th>Client</th><th>Amount</th><th>Status</th><th>Date</th><th>Actions</th></tr></thead>
    <tbody id="propTbody"><tr><td colspan="6" class="loading">Loading…</td></tr></tbody></table>
  </div>
</div>

<!-- INVOICES PAGE -->
<div class="page" id="page-invoices">
  <div style="margin-bottom:20px">
    <button class="btn btn-primary" onclick="openNewInvoice()">+ New Invoice</button>
  </div>
  <div class="table-card">
    <div class="table-header"><h3>Invoices</h3><span id="invCount" style="font-size:12px;color:var(--muted)"></span></div>
    <table><thead><tr><th>Invoice #</th><th>Client</th><th>Amount</th><th>Due Date</th><th>Status</th><th>Actions</th></tr></thead>
    <tbody id="invTbody"><tr><td colspan="6" class="loading">Loading…</td></tr></tbody></table>
  </div>
</div>

<!-- CLIENTS PAGE -->
<div class="page" id="page-clients">
  <div style="margin-bottom:20px">
    <button class="btn btn-primary" onclick="openNewClient()">+ Add Client</button>
  </div>
  <div class="table-card">
    <div class="table-header"><h3>Clients</h3><span id="clientCount" style="font-size:12px;color:var(--muted)"></span></div>
    <table><thead><tr><th>Name</th><th>Email</th><th>Company</th><th>Phone</th><th>Actions</th></tr></thead>
    <tbody id="clientTbody"><tr><td colspan="5" class="loading">Loading…</td></tr></tbody></table>
  </div>
</div>

<!-- SETTINGS PAGE -->
<div class="page" id="page-settings">
  <div class="table-card" style="padding:28px;max-width:560px">
    <h3 style="margin-bottom:20px;color:var(--white)">Profile & Business</h3>
    <div class="form-row">
      <div class="form-group"><label>Full Name</label><input type="text" id="setName"></div>
      <div class="form-group"><label>Business Name</label><input type="text" id="setBiz"></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Phone</label><input type="text" id="setPhone"></div>
      <div class="form-group"><label>Currency</label>
        <select id="setCurrency"><option value="NGN">NGN</option><option value="USD">USD</option><option value="GBP">GBP</option><option value="EUR">EUR</option></select>
      </div>
    </div>
    <h3 style="margin:24px 0 16px;color:var(--white)">Bank Details (for invoices)</h3>
    <div class="form-row">
      <div class="form-group"><label>Bank Name</label><input type="text" id="setBankName"></div>
      <div class="form-group"><label>Account Number</label><input type="text" id="setBankAcc"></div>
    </div>
    <div class="form-group"><label>Account Name</label><input type="text" id="setBankAccName"></div>
    <button class="btn btn-primary" onclick="saveProfile()">Save Changes</button>
    <div id="settingsAlert" style="margin-top:12px"></div>
  </div>
</div>

</div><!-- /content -->
</div><!-- /main -->

<!-- NEW PROPOSAL MODAL -->
<div class="overlay" id="proposalOverlay">
<div class="modal" style="max-width:640px">
  <h2 id="proposalModalTitle">🤖 AI Proposal Generator</h2>
  <div id="aiTab">
    <div class="form-row">
      <div class="form-group"><label>Client *</label><select id="pClient"><option value="">Select client…</option></select></div>
      <div class="form-group"><label>Service Type *</label><input type="text" id="pService" placeholder="e.g. Logo Design, Web Development"></div>
    </div>
    <div class="form-group"><label>Project Scope *</label><textarea id="pScope" placeholder="Describe what needs to be done in detail…"></textarea></div>
    <div class="form-row">
      <div class="form-group"><label>Budget Range</label><input type="text" id="pBudget" placeholder="e.g. ₦150,000"></div>
      <div class="form-group"><label>Tone</label><select id="pTone"><option value="professional">Professional</option><option value="friendly">Friendly</option><option value="formal">Formal</option></select></div>
    </div>
    <div id="aiResult" style="display:none">
      <div style="font-size:13px;font-weight:700;color:var(--green);margin-bottom:8px">✅ AI Draft Ready — Review before sending:</div>
      <div class="ai-result" id="aiContent"></div>
      <div style="font-size:12px;color:var(--muted);margin-top:8px" id="aiSuggestedTotal"></div>
    </div>
    <div class="form-actions">
      <button class="btn btn-outline" onclick="closeModal('proposalOverlay')">Cancel</button>
      <button class="btn btn-primary" onclick="generateAIProposal()" id="aiGenBtn">🤖 Generate with AI</button>
      <button class="btn btn-green" onclick="saveAIProposal()" id="aiSaveBtn" style="display:none">Save & Send →</button>
    </div>
  </div>
</div>
</div>

<!-- NEW INVOICE MODAL -->
<div class="overlay" id="invoiceOverlay">
<div class="modal" style="max-width:620px">
  <h2>Create Invoice</h2>
  <div class="form-row">
    <div class="form-group"><label>Client *</label><select id="iClient"><option value="">Select client…</option></select></div>
    <div class="form-group"><label>Currency</label><select id="iCurrency"><option value="NGN">NGN</option><option value="USD">USD</option><option value="GBP">GBP</option><option value="EUR">EUR</option></select></div>
  </div>
  <div class="form-group"><label>Title (optional)</label><input type="text" id="iTitle" placeholder="e.g. Website Design Services"></div>
  <div style="margin-bottom:12px">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
      <label style="font-size:12px;font-weight:600;color:var(--muted)">LINE ITEMS *</label>
      <button class="btn btn-outline btn-sm" onclick="addItem()">+ Add Item</button>
    </div>
    <div style="display:grid;grid-template-columns:3fr 1fr 1.5fr auto;gap:6px;margin-bottom:6px">
      <span style="font-size:11px;color:var(--muted)">Description</span><span style="font-size:11px;color:var(--muted)">Qty</span>
      <span style="font-size:11px;color:var(--muted)">Unit Price</span><span></span>
    </div>
    <div id="itemRows"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Tax Rate (%)</label><input type="number" id="iTax" value="0" min="0" max="100" onchange="calcTotal()"></div>
    <div class="form-group"><label>Discount</label><input type="number" id="iDiscount" value="0" min="0" onchange="calcTotal()"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Due Date</label><input type="date" id="iDue"></div>
    <div class="form-group"><label>Auto Reminders</label><select id="iReminders"><option value="true">Enabled (recommended)</option><option value="false">Disabled</option></select></div>
  </div>
  <div class="form-group"><label>Notes</label><input type="text" id="iNotes" placeholder="Payment terms, thank you message…"></div>
  <div style="background:var(--card2);border-radius:8px;padding:14px;margin-bottom:14px">
    <div style="display:flex;justify-content:space-between;font-size:13px;color:var(--muted);margin-bottom:4px">
      <span>Subtotal</span><span id="iSubtotal">0.00</span></div>
    <div style="display:flex;justify-content:space-between;font-size:13px;color:var(--muted);margin-bottom:4px">
      <span>Tax</span><span id="iTaxAmt">0.00</span></div>
    <div style="display:flex;justify-content:space-between;font-size:15px;font-weight:800;color:var(--white);border-top:1px solid var(--border);padding-top:8px;margin-top:8px">
      <span>Total</span><span id="iTotal">0.00</span></div>
  </div>
  <div class="form-actions">
    <button class="btn btn-outline" onclick="closeModal('invoiceOverlay')">Cancel</button>
    <button class="btn btn-primary" onclick="saveInvoice()">Create & Send Invoice →</button>
  </div>
</div>
</div>

<!-- NEW CLIENT MODAL -->
<div class="overlay" id="clientOverlay">
<div class="modal">
  <h2>Add Client</h2>
  <div class="form-row">
    <div class="form-group"><label>Name *</label><input type="text" id="cName" placeholder="John Doe"></div>
    <div class="form-group"><label>Email *</label><input type="email" id="cEmail" placeholder="client@company.com"></div>
  </div>
  <div class="form-row">
    <div class="form-group"><label>Phone</label><input type="text" id="cPhone" placeholder="+234 800 000 0000"></div>
    <div class="form-group"><label>Company</label><input type="text" id="cCompany" placeholder="Company Ltd"></div>
  </div>
  <div class="form-group"><label>Address</label><input type="text" id="cAddress" placeholder="City, Country"></div>
  <div class="form-actions">
    <button class="btn btn-outline" onclick="closeModal('clientOverlay')">Cancel</button>
    <button class="btn btn-green" onclick="saveClient()">Add Client ✓</button>
  </div>
</div>
</div>

<script>
const API = window.location.origin;
let TOKEN = localStorage.getItem('pp_token');
let USER = JSON.parse(localStorage.getItem('pp_user')||'{}');
let CLIENTS = [];
let aiDraftData = null;

// Auth guard
if(!TOKEN){ window.location.href='/'; }

// Init
document.getElementById('sideUsername').textContent = USER.name || 'User';
document.getElementById('sideAvatar').textContent = (USER.name||'U')[0].toUpperCase();
document.getElementById('sidePlan').textContent = (USER.plan||'free').charAt(0).toUpperCase()+(USER.plan||'free').slice(1)+' Plan';

function authFetch(url, opts={}){
  opts.headers = {...(opts.headers||{}), 'Authorization': 'Bearer '+TOKEN, 'Content-Type': 'application/json'};
  return fetch(API+url, opts);
}

function showAlert(msg, type='success', el='alertBox'){
  const box = document.getElementById(el);
  if(box) box.innerHTML = `<div class="alert alert-${type}">${msg}</div>`;
  setTimeout(()=>{ if(box) box.innerHTML=''; }, 4000);
}

function fmt(amount, currency){ 
  const sym = {NGN:'₦',USD:'$',GBP:'£',EUR:'€'}[currency||USER.currency||'NGN']||'';
  return sym+(parseFloat(amount||0).toLocaleString('en-NG', {minimumFractionDigits:0}));
}

function badge(status){
  const map = {draft:'badge-draft',sent:'badge-sent',viewed:'badge-viewed',paid:'badge-paid',
               overdue:'badge-overdue',accepted:'badge-accepted',declined:'badge-declined',partial:'badge-viewed'};
  return `<span class="badge ${map[status]||'badge-draft'}">${status}</span>`;
}

function showPage(page){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('page-'+page).classList.add('active');
  document.querySelectorAll('.nav-item').forEach(n=>{ if(n.textContent.trim().toLowerCase().includes(page.slice(0,4).toLowerCase())) n.classList.add('active'); });
  document.getElementById('pageTitle').textContent = page.charAt(0).toUpperCase()+page.slice(1);
  const actions = {proposals:'+ Proposal', invoices:'+ Invoice', clients:'+ Client', overview:'', settings:''};
  document.getElementById('topbarAction').textContent = actions[page]||'+ New';
  if(page==='overview') loadOverview();
  if(page==='proposals') loadProposals();
  if(page==='invoices') loadInvoices();
  if(page==='clients') loadClients();
  if(page==='settings') loadSettings();
}

function topbarActionFn(){
  const active = document.querySelector('.page.active').id.replace('page-','');
  if(active==='proposals') openNewProposal();
  if(active==='invoices') openNewInvoice();
  if(active==='clients') openNewClient();
}

// ── OVERVIEW ─────────────────────────────────────────────────────────────────
async function loadOverview(){
  try{
    const r = await authFetch('/dashboard/stats');
    const s = await r.json();
    const cur = s.currency||USER.currency||'NGN';
    document.getElementById('statInvoiced').textContent = fmt(s.total_invoiced, cur);
    document.getElementById('statPaid').textContent = fmt(s.total_paid, cur);
    document.getElementById('statPending').textContent = fmt(s.total_pending, cur);
    document.getElementById('statOverdue').textContent = fmt(s.total_overdue, cur);
    drawChart(s.monthly_revenue||[], cur);
    if(s.overdue_count>0) showAlert(`⚠️ You have ${s.overdue_count} overdue invoice(s) totaling ${fmt(s.total_overdue,cur)}. <button onclick="showPage('invoices')" style="background:transparent;border:none;color:var(--yellow);cursor:pointer;font-weight:700;text-decoration:underline">View Invoices →</button>`,'info');
  }catch(e){}
  loadInsights();
  loadRecent();
}

async function loadInsights(){
  const box = document.getElementById('aiInsights');
  try{
    const r = await authFetch('/dashboard/insights');
    const d = await r.json();
    box.innerHTML = d.insights.replace(/\\n/g,'<br>').replace(/\\*\\*(.*?)\\*\\*/g,'<strong>$1</strong>');
  }catch(e){ box.textContent = 'Could not load insights.'; }
}

async function loadRecent(){
  try{
    const r = await authFetch('/dashboard/recent');
    const items = await r.json();
    const tbody = document.getElementById('recentTbody');
    if(!items.length){ tbody.innerHTML='<tr><td colspan="5" class="empty"><div class="empty-icon">📭</div>No activity yet. Create your first proposal or invoice!</td></tr>'; return; }
    tbody.innerHTML = items.map(i=>`<tr>
      <td>${i.type==='invoice'?'🧾 Invoice':'📄 Proposal'}</td>
      <td>${i.title}</td>
      <td>${fmt(i.amount,i.currency)}</td>
      <td>${badge(i.status)}</td>
      <td>${i.date?.slice(0,10)||'—'}</td>
    </tr>`).join('');
  }catch(e){}
}

function drawChart(months, currency){
  const el = document.getElementById('revenueChart');
  if(!months?.length){ el.innerHTML='<div style="color:var(--muted);font-size:13px;padding:20px">No data yet</div>'; return; }
  const max = Math.max(...months.map(m=>m.revenue||0), 1);
  el.innerHTML = months.map(m=>{
    const h = Math.max(4, Math.round((m.revenue/max)*120));
    return `<div class="bar-wrap"><div class="bar" style="height:${h}px" title="${fmt(m.revenue,currency)}"></div><div class="bar-label">${m.month}</div></div>`;
  }).join('');
}

// ── PROPOSALS ────────────────────────────────────────────────────────────────
async function loadProposals(){
  const tbody = document.getElementById('propTbody');
  try{
    await loadClientsData();
    const r = await authFetch('/proposals');
    const props = await r.json();
    document.getElementById('propCount').textContent = props.length+' proposals';
    if(!props.length){ tbody.innerHTML='<tr><td colspan="6" class="empty"><div class="empty-icon">📄</div>No proposals yet. Create your first AI proposal!</td></tr>'; return; }
    tbody.innerHTML = props.map(p=>{
      const client = CLIENTS.find(c=>c.id===p.client_id);
      const viewUrl = `${window.location.origin}/p/${p.public_token}`;
      return `<tr>
        <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${p.title}</td>
        <td>${client?.name||'—'}</td>
        <td>${fmt(p.total_amount,p.currency)}</td>
        <td>${badge(p.status)}</td>
        <td>${p.created_at?.slice(0,10)||'—'}</td>
        <td style="display:flex;gap:6px">
          ${p.status==='draft'?`<button class="btn btn-primary btn-sm" onclick="sendProposal('${p.id}')">Send</button>`:''}
          <button class="btn btn-outline btn-sm" onclick="copyLink('${viewUrl}')">📋</button>
          <button class="btn btn-red btn-sm" onclick="deleteProposal('${p.id}')">🗑</button>
        </td>
      </tr>`;
    }).join('');
  }catch(e){ tbody.innerHTML='<tr><td colspan="6" style="color:var(--red);padding:20px">Error loading proposals</td></tr>'; }
}

async function sendProposal(id){
  if(!confirm('Send this proposal to the client?')) return;
  const r = await authFetch(`/proposals/${id}/send`,{method:'POST'});
  const d = await r.json();
  showAlert(d.message||'Proposal sent!');
  loadProposals();
}
async function deleteProposal(id){
  if(!confirm('Delete this proposal?')) return;
  await authFetch(`/proposals/${id}`,{method:'DELETE'});
  loadProposals();
}

// ── INVOICES ─────────────────────────────────────────────────────────────────
async function loadInvoices(){
  const tbody = document.getElementById('invTbody');
  try{
    await loadClientsData();
    const r = await authFetch('/invoices');
    const invs = await r.json();
    document.getElementById('invCount').textContent = invs.length+' invoices';
    if(!invs.length){ tbody.innerHTML='<tr><td colspan="6" class="empty"><div class="empty-icon">🧾</div>No invoices yet. Create your first invoice!</td></tr>'; return; }
    tbody.innerHTML = invs.map(inv=>{
      const client = CLIENTS.find(c=>c.id===inv.client_id);
      return `<tr>
        <td>${inv.invoice_number}</td>
        <td>${client?.name||'—'}</td>
        <td style="font-weight:700">${fmt(inv.total,inv.currency)}</td>
        <td style="color:${inv.due_date<new Date().toISOString().slice(0,10)&&inv.status!=='paid'?'var(--red)':'var(--muted)'}">${inv.due_date||'—'}</td>
        <td>${badge(inv.status)}</td>
        <td style="display:flex;gap:4px">
          ${inv.status!=='paid'?`<button class="btn btn-primary btn-sm" onclick="sendReminder('${inv.id}','${client?.name||'client'}')">Remind</button>`:''}
          ${inv.status!=='paid'?`<button class="btn btn-green btn-sm" onclick="markPaid('${inv.id}')">Paid ✓</button>`:''}
          <button class="btn btn-red btn-sm" onclick="deleteInvoice('${inv.id}')">🗑</button>
        </td>
      </tr>`;
    }).join('');
  }catch(e){ tbody.innerHTML='<tr><td colspan="6" style="color:var(--red);padding:20px">Error loading invoices</td></tr>'; }
}

async function sendReminder(id, name){
  if(!confirm(`Send AI payment reminder to ${name}?`)) return;
  const r = await authFetch(`/invoices/${id}/remind`,{method:'POST'});
  const d = await r.json();
  showAlert(d.message||'Reminder sent!');
}
async function markPaid(id){
  if(!confirm('Mark this invoice as paid?')) return;
  await authFetch(`/invoices/${id}/mark-paid`,{method:'POST'});
  showAlert('Invoice marked as paid ✓');
  loadInvoices();
}
async function deleteInvoice(id){
  if(!confirm('Delete this invoice?')) return;
  await authFetch(`/invoices/${id}`,{method:'DELETE'});
  loadInvoices();
}

// ── CLIENTS ──────────────────────────────────────────────────────────────────
async function loadClientsData(){
  try{
    const r = await authFetch('/clients');
    CLIENTS = await r.json();
    // Fill selects
    ['pClient','iClient'].forEach(sel=>{
      const el = document.getElementById(sel);
      if(!el) return;
      const cur = el.value;
      el.innerHTML = '<option value="">Select client…</option>'+CLIENTS.map(c=>`<option value="${c.id}">${c.name} (${c.email})</option>`).join('');
      if(cur) el.value = cur;
    });
  }catch(e){}
}

async function loadClients(){
  const tbody = document.getElementById('clientTbody');
  await loadClientsData();
  document.getElementById('clientCount').textContent = CLIENTS.length+' clients';
  if(!CLIENTS.length){ tbody.innerHTML='<tr><td colspan="5" class="empty"><div class="empty-icon">👥</div>No clients yet. Add your first client!</td></tr>'; return; }
  tbody.innerHTML = CLIENTS.map(c=>`<tr>
    <td style="font-weight:600">${c.name}</td>
    <td>${c.email}</td>
    <td>${c.company||'—'}</td>
    <td>${c.phone||'—'}</td>
    <td><button class="btn btn-red btn-sm" onclick="deleteClient('${c.id}')">🗑</button></td>
  </tr>`).join('');
}

async function deleteClient(id){
  if(!confirm('Delete this client?')) return;
  await authFetch(`/clients/${id}`,{method:'DELETE'});
  loadClients();
}

// ── MODALS ───────────────────────────────────────────────────────────────────
function openModal(id){ document.getElementById(id).classList.add('open'); }
function closeModal(id){ document.getElementById(id).classList.remove('open'); }

function openNewProposal(ai=true){
  document.getElementById('proposalModalTitle').textContent = ai?'🤖 AI Proposal Generator':'📄 New Proposal';
  document.getElementById('aiResult').style.display='none';
  document.getElementById('aiSaveBtn').style.display='none';
  document.getElementById('aiGenBtn').style.display='inline-flex';
  aiDraftData=null;
  loadClientsData();
  openModal('proposalOverlay');
}

async function generateAIProposal(){
  const svc = document.getElementById('pService').value.trim();
  const scope = document.getElementById('pScope').value.trim();
  if(!svc||!scope){ alert('Please enter service type and scope.'); return; }
  const btn = document.getElementById('aiGenBtn');
  btn.textContent='⏳ Generating…'; btn.disabled=true;
  try{
    const payload = {
      client_id: document.getElementById('pClient').value||null,
      service_type: svc, scope: scope,
      budget: document.getElementById('pBudget').value||null,
      tone: document.getElementById('pTone').value
    };
    const r = await authFetch('/proposals/ai-draft',{method:'POST',body:JSON.stringify(payload)});
    const d = await r.json();
    aiDraftData = d;
    document.getElementById('aiContent').textContent = d.content;
    document.getElementById('aiSuggestedTotal').textContent = d.suggested_total>0?`Suggested total: ${fmt(d.suggested_total, USER.currency||'NGN')}`:'';
    document.getElementById('aiResult').style.display='block';
    document.getElementById('aiSaveBtn').style.display='inline-flex';
  }catch(e){ alert('AI generation failed. Check your API key.'); }
  btn.textContent='🔄 Regenerate'; btn.disabled=false;
}

async function saveAIProposal(){
  if(!aiDraftData) return;
  const clientId = document.getElementById('pClient').value;
  const clientName = CLIENTS.find(c=>c.id===clientId)?.name||'Client';
  const payload = {
    title: aiDraftData.title||`${document.getElementById('pService').value} Proposal for ${clientName}`,
    client_id: clientId||null,
    content: aiDraftData.content,
    services: aiDraftData.services||[],
    total_amount: aiDraftData.suggested_total||0,
    currency: USER.currency||'NGN'
  };
  const r = await authFetch('/proposals',{method:'POST',body:JSON.stringify(payload)});
  const d = await r.json();
  closeModal('proposalOverlay');
  showAlert(`Proposal saved! ${clientId?'Sending to client…':''}`);
  if(clientId && d.id) sendProposal(d.id);
  else loadProposals();
}

function openNewInvoice(){
  document.getElementById('itemRows').innerHTML='';
  document.getElementById('iDue').value = new Date(Date.now()+14*86400000).toISOString().slice(0,10);
  loadClientsData();
  addItem(); addItem();
  calcTotal();
  openModal('invoiceOverlay');
}

let itemIdx=0;
function addItem(){
  itemIdx++;
  const row = document.createElement('div');
  row.className='item-row'; row.id='item-'+itemIdx;
  row.innerHTML=`<input type="text" placeholder="Description" id="idesc-${itemIdx}">
    <input type="number" placeholder="1" value="1" min="0.01" step="0.01" id="iqty-${itemIdx}" onchange="calcTotal()">
    <input type="number" placeholder="0.00" min="0" step="0.01" id="iprice-${itemIdx}" onchange="calcTotal()">
    <button class="remove-btn" onclick="document.getElementById('item-${itemIdx}').remove();calcTotal()">✕</button>`;
  document.getElementById('itemRows').appendChild(row);
}

function calcTotal(){
  let sub=0;
  document.querySelectorAll('.item-row').forEach(row=>{
    const id=row.id.split('-')[1];
    const qty=parseFloat(document.getElementById('iqty-'+id)?.value)||0;
    const price=parseFloat(document.getElementById('iprice-'+id)?.value)||0;
    sub+=qty*price;
  });
  const tax=parseFloat(document.getElementById('iTax')?.value)||0;
  const disc=parseFloat(document.getElementById('iDiscount')?.value)||0;
  const taxAmt=sub*(tax/100);
  const total=sub+taxAmt-disc;
  const cur=document.getElementById('iCurrency')?.value||USER.currency||'NGN';
  document.getElementById('iSubtotal').textContent=fmt(sub,cur);
  document.getElementById('iTaxAmt').textContent=fmt(taxAmt,cur);
  document.getElementById('iTotal').textContent=fmt(total,cur);
}

async function saveInvoice(){
  const clientId = document.getElementById('iClient').value;
  if(!clientId){ alert('Please select a client'); return; }
  const items=[];
  document.querySelectorAll('.item-row').forEach(row=>{
    const id=row.id.split('-')[1];
    const desc=document.getElementById('idesc-'+id)?.value.trim();
    const qty=parseFloat(document.getElementById('iqty-'+id)?.value)||1;
    const price=parseFloat(document.getElementById('iprice-'+id)?.value)||0;
    if(desc&&price>0) items.push({description:desc,quantity:qty,unit_price:price});
  });
  if(!items.length){ alert('Please add at least one line item with a price'); return; }
  const payload={
    client_id:clientId,
    title:document.getElementById('iTitle').value||null,
    items, currency:document.getElementById('iCurrency').value,
    tax_rate:parseFloat(document.getElementById('iTax').value)||0,
    discount:parseFloat(document.getElementById('iDiscount').value)||0,
    due_date:document.getElementById('iDue').value||null,
    notes:document.getElementById('iNotes').value||null,
    auto_reminders:document.getElementById('iReminders').value==='true'
  };
  const r=await authFetch('/invoices',{method:'POST',body:JSON.stringify(payload)});
  const inv=await r.json();
  if(inv.id){
    const sr=await authFetch(`/invoices/${inv.id}/send`,{method:'POST'});
    const sd=await sr.json();
    closeModal('invoiceOverlay');
    showAlert(sd.message||`Invoice ${inv.invoice_number} created and sent!`);
    if(sd.payment_url) window.open(sd.payment_url,'_blank');
    loadInvoices();
  }else{ alert(JSON.stringify(inv)); }
}

function openNewClient(){ openModal('clientOverlay'); }
async function saveClient(){
  const name=document.getElementById('cName').value.trim();
  const email=document.getElementById('cEmail').value.trim();
  if(!name||!email){ alert('Name and email are required'); return; }
  const r=await authFetch('/clients',{method:'POST',body:JSON.stringify({
    name,email,phone:document.getElementById('cPhone').value||null,
    company:document.getElementById('cCompany').value||null,
    address:document.getElementById('cAddress').value||null
  })});
  const d=await r.json();
  closeModal('clientOverlay');
  showAlert(`Client ${d.name} added!`);
  loadClients();
}

// ── SETTINGS ─────────────────────────────────────────────────────────────────
async function loadSettings(){
  const r=await authFetch('/auth/me');
  const u=await r.json();
  document.getElementById('setName').value=u.name||'';
  document.getElementById('setBiz').value=u.business_name||'';
  document.getElementById('setPhone').value=u.phone||'';
  document.getElementById('setCurrency').value=u.currency||'NGN';
  document.getElementById('setBankName').value=u.bank_name||'';
  document.getElementById('setBankAcc').value=u.bank_account||'';
  document.getElementById('setBankAccName').value=u.bank_account_name||'';
}
async function saveProfile(){
  const data={
    name:document.getElementById('setName').value,
    business_name:document.getElementById('setBiz').value,
    phone:document.getElementById('setPhone').value,
    currency:document.getElementById('setCurrency').value,
    bank_name:document.getElementById('setBankName').value,
    bank_account:document.getElementById('setBankAcc').value,
    bank_account_name:document.getElementById('setBankAccName').value
  };
  const r=await authFetch('/auth/profile',{method:'PUT',body:JSON.stringify(data)});
  const d=await r.json();
  showAlert('Profile saved ✓','success','settingsAlert');
  USER={...USER,...data};
  localStorage.setItem('pp_user',JSON.stringify(USER));
  document.getElementById('sideUsername').textContent=USER.name||'User';
}

function copyLink(url){ navigator.clipboard.writeText(url); showAlert('Link copied to clipboard!'); }
function logout(){ localStorage.removeItem('pp_token');localStorage.removeItem('pp_user');window.location.href='/'; }

document.querySelectorAll('.overlay').forEach(o=>o.addEventListener('click',function(e){ if(e.target===this) this.classList.remove('open'); }));

loadOverview();
</script>
</body>
</html>
"""
