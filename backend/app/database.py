"""PropelPay Database Setup"""
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _fix_db_url(url: str) -> str:
    """Convert Render's postgres:// to SQLAlchemy async format."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _make_engine():
    url = _fix_db_url(settings.DATABASE_URL)
    if "sqlite" in url:
        return create_async_engine(
            url, echo=settings.DEBUG,
            connect_args={"check_same_thread": False}
        )
    return create_async_engine(url, echo=False, poolclass=NullPool)


engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Lightweight migrations — this project has no Alembic, and Base.metadata.create_all()
# only creates tables that don't exist yet, it never adds new columns to a table that
# already exists in production. Any time a new column is added to a model, add the
# matching statement here. Each statement is wrapped so a column that already exists
# (fresh installs where create_all() made it right the first time) is silently skipped.
_MIGRATIONS = [
    "ALTER TABLE invoices ADD COLUMN reminder_stage INTEGER DEFAULT 0",
    "ALTER TABLE invoices ADD COLUMN late_fee_enabled BOOLEAN DEFAULT FALSE",
    "ALTER TABLE invoices ADD COLUMN late_fee_percent FLOAT DEFAULT 0.0",
    "ALTER TABLE invoices ADD COLUMN late_fee_applied BOOLEAN DEFAULT FALSE",
]


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Run column migrations in their own transaction so a failed/duplicate ALTER
    # on one statement can't roll back the others (Postgres aborts the whole
    # transaction on first error otherwise).
    for stmt in _MIGRATIONS:
        try:
            async with engine.begin() as conn:
                from sqlalchemy import text
                await conn.execute(text(stmt))
        except Exception:
            pass
