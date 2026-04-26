from decimal import Decimal

import pytest

from app.application.commands import (
    AssignEquipmentCommand,
    CreateEquipmentCommand,
    TransferEquipmentCommand,
    UnassignEquipmentCommand,
    UpdateEquipmentCommand,
)
from app.application.services import EquipmentService
from app.domain.entities import Category
from app.domain.enums import EquipmentStatus
from app.domain.errors import ConflictError, NotFoundError


@pytest.fixture
def service(uow_factory) -> EquipmentService:
    return EquipmentService(uow_factory)


def _create_cmd(**kwargs) -> CreateEquipmentCommand:
    defaults = dict(inventory_number="INV-1", name="Laptop", category_id=1)
    defaults.update(kwargs)
    return CreateEquipmentCommand(**defaults)


async def test_create_equipment_success(service: EquipmentService, seeded_category: Category) -> None:
    eq = await service.create(_create_cmd())
    assert eq.id is not None
    assert eq.name == "Laptop"
    assert eq.status == EquipmentStatus.IN_STOCK


async def test_create_duplicate_inventory_number_raises(
    service: EquipmentService, seeded_category: Category
) -> None:
    await service.create(_create_cmd(inventory_number="INV-1"))
    with pytest.raises(ConflictError):
        await service.create(_create_cmd(inventory_number="INV-1"))


async def test_create_with_missing_category_raises(service: EquipmentService) -> None:
    with pytest.raises(NotFoundError):
        await service.create(_create_cmd(category_id=999))


async def test_get_existing_equipment(
    service: EquipmentService, seeded_equipment
) -> None:
    result = await service.get(1)
    assert result.name == "MacBook Pro"


async def test_get_nonexistent_raises(service: EquipmentService) -> None:
    with pytest.raises(NotFoundError):
        await service.get(9999)


async def test_assign_creates_movement(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd(inventory_number="INV-2"))
    movement = await service.assign(
        AssignEquipmentCommand(equipment_id=eq.id, employee_id=77)
    )
    assert movement.movement_type.value == "assign"
    assert movement.to_employee_id == 77
    assert movement.from_employee_id is None


async def test_transfer_creates_movement(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    await service.assign(AssignEquipmentCommand(equipment_id=eq.id, employee_id=10))
    movement = await service.transfer(
        TransferEquipmentCommand(equipment_id=eq.id, to_employee_id=20)
    )
    assert movement.movement_type.value == "transfer"
    assert movement.from_employee_id == 10
    assert movement.to_employee_id == 20


async def test_unassign_creates_movement(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    await service.assign(AssignEquipmentCommand(equipment_id=eq.id, employee_id=55))
    movement = await service.unassign(UnassignEquipmentCommand(equipment_id=eq.id))
    assert movement.movement_type.value == "unassign"
    assert movement.from_employee_id == 55
    assert movement.to_employee_id is None


async def test_delete_assigned_equipment_raises(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    await service.assign(AssignEquipmentCommand(equipment_id=eq.id, employee_id=1))
    with pytest.raises(ConflictError, match="Assigned"):
        await service.delete(eq.id)


async def test_delete_equipment_with_history_raises(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    await service.assign(AssignEquipmentCommand(equipment_id=eq.id, employee_id=1))
    await service.unassign(UnassignEquipmentCommand(equipment_id=eq.id))
    with pytest.raises(ConflictError, match="movement history"):
        await service.delete(eq.id)


async def test_delete_clean_equipment_succeeds(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    await service.delete(eq.id)
    with pytest.raises(NotFoundError):
        await service.get(eq.id)


async def test_update_name(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    updated = await service.update(UpdateEquipmentCommand(equipment_id=eq.id, name="Desktop"))
    assert updated.name == "Desktop"


async def test_update_purchase_cost_amount_only(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(
        _create_cmd(purchase_cost_amount=1000.0, purchase_cost_currency="USD")
    )
    updated = await service.update(
        UpdateEquipmentCommand(equipment_id=eq.id, purchase_cost_amount=1500.0)
    )
    assert updated.purchase_cost is not None
    assert updated.purchase_cost.amount == Decimal("1500.00")
    assert updated.purchase_cost.currency == "USD"


async def test_update_purchase_cost_currency_only(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(
        _create_cmd(purchase_cost_amount=999.0, purchase_cost_currency="USD")
    )
    updated = await service.update(
        UpdateEquipmentCommand(equipment_id=eq.id, purchase_cost_currency="EUR")
    )
    assert updated.purchase_cost is not None
    assert updated.purchase_cost.currency == "EUR"
    assert updated.purchase_cost.amount == Decimal("999.00")


async def test_update_clear_purchase_cost(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(
        _create_cmd(purchase_cost_amount=500.0, purchase_cost_currency="USD")
    )
    updated = await service.update(
        UpdateEquipmentCommand(equipment_id=eq.id, purchase_cost_amount=None)
    )
    assert updated.purchase_cost is None


async def test_history_returns_all_movements(
    service: EquipmentService, seeded_category: Category
) -> None:
    eq = await service.create(_create_cmd())
    await service.assign(AssignEquipmentCommand(equipment_id=eq.id, employee_id=1))
    await service.transfer(TransferEquipmentCommand(equipment_id=eq.id, to_employee_id=2))
    await service.unassign(UnassignEquipmentCommand(equipment_id=eq.id))

    history = await service.history(eq.id)
    types = [m.movement_type.value for m in history]
    assert types == ["assign", "transfer", "unassign"]
