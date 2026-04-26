from __future__ import annotations

import pytest

from app.application.queries import EquipmentFilters
from app.domain.entities import Category, Equipment
from app.domain.value_objects import InventoryNumber


class FakeCategoryRepo:
    def __init__(self) -> None:
        self._items: dict[int, Category] = {}
        self._next_id = 1

    async def add(self, category: Category) -> Category:
        if category.id is None:
            category.id = self._next_id
            self._next_id += 1
        self._items[category.id] = category
        return category

    async def get(self, category_id: int) -> Category | None:
        return self._items.get(category_id)

    async def get_by_name(self, name: str) -> Category | None:
        return next((c for c in self._items.values() if c.name == name), None)

    async def list(self, *, skip: int, limit: int) -> tuple[list[Category], int]:
        items = list(self._items.values())
        return items[skip : skip + limit], len(items)

    async def delete(self, category_id: int) -> None:
        self._items.pop(category_id, None)


class FakeEquipmentRepo:
    def __init__(self) -> None:
        self._items: dict[int, Equipment] = {}
        self._next_id = 1

    async def add(self, equipment: Equipment) -> Equipment:
        if equipment.id is None:
            equipment.id = self._next_id
            self._next_id += 1
        self._items[equipment.id] = equipment
        return equipment

    async def get(self, equipment_id: int) -> Equipment | None:
        return self._items.get(equipment_id)

    async def get_by_inventory_number(self, inventory_number: str) -> Equipment | None:
        return next(
            (e for e in self._items.values() if str(e.inventory_number) == inventory_number),
            None,
        )

    async def list(self, filters: EquipmentFilters) -> tuple[list[Equipment], int]:
        items = list(self._items.values())
        if filters.category_id is not None:
            items = [e for e in items if e.category_id == filters.category_id]
        if filters.status is not None:
            items = [e for e in items if e.status == filters.status]
        total = len(items)
        return items[filters.skip : filters.skip + filters.limit], total

    async def delete(self, equipment_id: int) -> None:
        self._items.pop(equipment_id, None)


class FakeMovementRepo:
    def __init__(self) -> None:
        self._items: list = []
        self._next_id = 1

    async def add(self, movement) -> object:
        movement.id = self._next_id
        self._next_id += 1
        self._items.append(movement)
        return movement

    async def list_by_equipment(self, equipment_id: int) -> list:
        return [m for m in self._items if m.equipment_id == equipment_id]

    async def has_movements_for_equipment(self, equipment_id: int) -> bool:
        return any(m.equipment_id == equipment_id for m in self._items)


class FakeUoW:
    def __init__(
        self,
        *,
        categories: FakeCategoryRepo | None = None,
        equipments: FakeEquipmentRepo | None = None,
        movements: FakeMovementRepo | None = None,
    ) -> None:
        self.categories = categories or FakeCategoryRepo()
        self.equipments = equipments or FakeEquipmentRepo()
        self.movements = movements or FakeMovementRepo()

    async def __aenter__(self) -> FakeUoW:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        pass

    async def commit(self) -> None:
        pass

    async def rollback(self) -> None:
        pass


@pytest.fixture
def fake_categories() -> FakeCategoryRepo:
    return FakeCategoryRepo()


@pytest.fixture
def fake_equipment() -> FakeEquipmentRepo:
    return FakeEquipmentRepo()


@pytest.fixture
def fake_movements() -> FakeMovementRepo:
    return FakeMovementRepo()


@pytest.fixture
def fake_uow(
    fake_categories: FakeCategoryRepo,
    fake_equipment: FakeEquipmentRepo,
    fake_movements: FakeMovementRepo,
) -> FakeUoW:
    return FakeUoW(
        categories=fake_categories,
        equipments=fake_equipment,
        movements=fake_movements,
    )


@pytest.fixture
def uow_factory(fake_uow: FakeUoW):
    def factory():
        return fake_uow

    return factory


@pytest.fixture
def seeded_category(fake_categories: FakeCategoryRepo) -> Category:
    category = Category.create(name="Laptops", description="Portable workstations")
    category.id = 1
    fake_categories._items[1] = category
    return category


@pytest.fixture
def seeded_equipment(fake_equipment: FakeEquipmentRepo, seeded_category: Category) -> Equipment:
    eq = Equipment.create(
        inventory_number=InventoryNumber("LT-001"),
        name="MacBook Pro",
        category_id=1,
    )
    eq.id = 1
    fake_equipment._items[1] = eq
    return eq
