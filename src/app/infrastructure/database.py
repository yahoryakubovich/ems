from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.infrastructure.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, future=True, echo=False)
SessionFactory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
