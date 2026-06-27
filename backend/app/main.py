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
    logger.info("PropelPay API v1.0 starting…")
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
    return {"status": "ok", "service": "PropelPay API", "version": "1.0.0"}

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    """Serve landing page."""
    for path in ["/app/propelpay/frontend/index.html", "frontend/index.html", "../frontend/index.html"]:
        if os.path.exists(path):
            with open(path) as f: return HTMLResponse(f.read())
    return HTMLResponse("<h1>PropelPay API</h1><p>Visit /docs for API reference.</p>")
