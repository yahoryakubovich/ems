from functools import lru_cache

from app.application.services import CategoryService, EquipmentService
from app.infrastructure.uow import SqlAlchemyUnitOfWork


def get_uow() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork()


@lru_cache(maxsize=1)
def get_category_service() -> CategoryService:
    return CategoryService(get_uow)


@lru_cache(maxsize=1)
def get_equipment_service() -> EquipmentService:
    return EquipmentService(get_uow)
