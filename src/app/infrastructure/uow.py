from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.ports import UnitOfWork
from app.infrastructure.database import SessionFactory
from app.infrastructure.repositories import (
    SqlAlchemyCategoryRepository,
    SqlAlchemyEquipmentRepository,
    SqlAlchemyMovementRepository,
)


class SqlAlchemyUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession] = SessionFactory):
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> UnitOfWork:
        self._session = self._session_factory()
        self.categories = SqlAlchemyCategoryRepository(self._session)
        self.equipments = SqlAlchemyEquipmentRepository(self._session)
        self.movements = SqlAlchemyMovementRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
        finally:
            await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
