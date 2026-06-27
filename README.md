# ⚡ PropelPay — Send. Sign. Get Paid.

> The all-in-one platform for freelancers and agencies to send AI proposals, collect e-signatures, invoice clients and get paid automatically.

## Quick Start (5 minutes)

```bash
git clone https://github.com/YOUR_REPO/propelpay
cd propelpay
cp .env.example .env
# Edit .env with your keys
docker-compose up -d
# Open http://localhost:8000
```

## Required API Keys

| Key | Where to get it | Cost |
|-----|----------------|------|
| GROQ_API_KEY | console.groq.com | FREE |
| PAYSTACK_SECRET_KEY | paystack.com/settings | FREE |
| SMTP (Gmail) | Google Account → App Passwords | FREE |
| JWT_SECRET_KEY | Any random string | — |
| DATABASE_URL | SQLite default (no setup) | FREE |

## Tech Stack

- *Backend:* FastAPI (Python 3.11)
- *Database:* SQLite (dev) / PostgreSQL (prod)
- *AI:* Groq (Llama 3 70B) — Free tier
- *Payments:* Paystack
- *Email:* SMTP (Gmail)
- *Deploy:* Docker / Oracle Cloud Always Free

## API Documentation

Visit `/docs` for interactive Swagger API docs.

## Deployment (Oracle Cloud Always Free)

See DEPLOY.md for full step-by-step instructions.
