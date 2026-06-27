"""PropelPay Database Setup"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


def _make_engine():
    url = settings.DATABASE_URL
    if "sqlite" in url:
        return create_async_engine(url, echo=settings.DEBUG, connect_args={"check_same_thread": False})
    return create_async_engine(url, echo=False, poolclass=NullPool)


engine = _make_engine()
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
