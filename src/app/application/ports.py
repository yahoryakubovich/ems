from __future__ import annotations

from abc import ABC, abstractmethod

from app.application.queries import EquipmentFilters
from app.domain.entities import Category, Equipment, EquipmentMovement


class CategoryRepository(ABC):
    @abstractmethod
    async def add(self, category: Category) -> Category:
        raise NotImplementedError

    @abstractmethod
    async def get(self, category_id: int) -> Category | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_name(self, name: str) -> Category | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, *, skip: int, limit: int) -> tuple[list[Category], int]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, category_id: int) -> None:
        raise NotImplementedError


class EquipmentRepository(ABC):
    @abstractmethod
    async def add(self, equipment: Equipment) -> Equipment:
        raise NotImplementedError

    @abstractmethod
    async def get(self, equipment_id: int) -> Equipment | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_inventory_number(self, inventory_number: str) -> Equipment | None:
        raise NotImplementedError

    @abstractmethod
    async def list(self, filters: EquipmentFilters) -> tuple[list[Equipment], int]:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, equipment_id: int) -> None:
        raise NotImplementedError


class MovementRepository(ABC):
    @abstractmethod
    async def add(self, movement: EquipmentMovement) -> EquipmentMovement:
        raise NotImplementedError

    @abstractmethod
    async def list_by_equipment(self, equipment_id: int) -> list[EquipmentMovement]:
        raise NotImplementedError

    @abstractmethod
    async def has_movements_for_equipment(self, equipment_id: int) -> bool:
        raise NotImplementedError


class UnitOfWork(ABC):
    categories: CategoryRepository
    equipments: EquipmentRepository
    movements: MovementRepository

    @abstractmethod
    async def __aenter__(self) -> UnitOfWork:
        raise NotImplementedError

    @abstractmethod
    async def __aexit__(self, exc_type, exc, tb) -> None:
        raise NotImplementedError

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
