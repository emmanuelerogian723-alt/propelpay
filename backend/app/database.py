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


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
