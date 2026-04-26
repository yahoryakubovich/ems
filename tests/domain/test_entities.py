from datetime import timezone

import pytest

from app.domain.entities import Equipment
from app.domain.enums import EquipmentStatus
from app.domain.errors import BusinessRuleViolation, ValidationError
from app.domain.value_objects import InventoryNumber


def build_equipment(status: EquipmentStatus = EquipmentStatus.IN_STOCK) -> Equipment:
    return Equipment.create(
        inventory_number=InventoryNumber("INV-1"),
        name="Laptop",
        category_id=1,
        status=status,
    )


class TestAssign:
    def test_changes_status_to_assigned(self) -> None:
        eq = build_equipment()
        eq.assign(42)
        assert eq.status == EquipmentStatus.ASSIGNED
        assert eq.assigned_to_employee_id == 42

    def test_updates_updated_at_timezone(self) -> None:
        eq = build_equipment()
        eq.assign(42)
        assert eq.updated_at.tzinfo == timezone.utc

    def test_retired_equipment_cannot_be_assigned(self) -> None:
        eq = build_equipment(EquipmentStatus.RETIRED)
        with pytest.raises(BusinessRuleViolation, match="Retired"):
            eq.assign(1)

    def test_maintenance_equipment_cannot_be_assigned(self) -> None:
        eq = build_equipment(EquipmentStatus.MAINTENANCE)
        with pytest.raises(BusinessRuleViolation, match="maintenance"):
            eq.assign(1)

    def test_already_assigned_equipment_raises(self) -> None:
        eq = build_equipment()
        eq.assign(10)
        with pytest.raises(BusinessRuleViolation, match="already assigned"):
            eq.assign(20)

    def test_invalid_employee_id_raises(self) -> None:
        eq = build_equipment()
        with pytest.raises(ValidationError, match="positive"):
            eq.assign(0)


class TestTransfer:
    def test_transfer_changes_employee(self) -> None:
        eq = build_equipment()
        eq.assign(10)
        previous = eq.transfer(20)
        assert previous == 10
        assert eq.assigned_to_employee_id == 20
        assert eq.status == EquipmentStatus.ASSIGNED

    def test_transfer_unassigned_raises(self) -> None:
        eq = build_equipment()
        with pytest.raises(BusinessRuleViolation, match="not assigned"):
            eq.transfer(100)

    def test_transfer_to_same_employee_raises(self) -> None:
        eq = build_equipment()
        eq.assign(42)
        with pytest.raises(BusinessRuleViolation, match="already assigned to this employee"):
            eq.transfer(42)


class TestUnassign:
    def test_unassign_returns_previous_employee(self) -> None:
        eq = build_equipment()
        eq.assign(55)
        previous = eq.unassign()
        assert previous == 55
        assert eq.assigned_to_employee_id is None
        assert eq.status == EquipmentStatus.IN_STOCK

    def test_unassign_not_assigned_raises(self) -> None:
        eq = build_equipment()
        with pytest.raises(BusinessRuleViolation, match="not assigned"):
            eq.unassign()


class TestChangeStatus:
    def test_cannot_change_status_while_assigned(self) -> None:
        eq = build_equipment()
        eq.assign(42)
        with pytest.raises(BusinessRuleViolation, match="while equipment is assigned"):
            eq.change_status(EquipmentStatus.MAINTENANCE)

    def test_retired_is_terminal(self) -> None:
        eq = build_equipment(EquipmentStatus.RETIRED)
        with pytest.raises(BusinessRuleViolation, match="Retired equipment cannot return"):
            eq.change_status(EquipmentStatus.IN_STOCK)

    def test_cannot_set_assigned_via_change_status(self) -> None:
        eq = build_equipment()
        with pytest.raises(BusinessRuleViolation, match="assign or transfer"):
            eq.change_status(EquipmentStatus.ASSIGNED)

    def test_in_stock_to_maintenance_allowed(self) -> None:
        eq = build_equipment()
        eq.change_status(EquipmentStatus.MAINTENANCE)
        assert eq.status == EquipmentStatus.MAINTENANCE

    def test_in_stock_to_retired_allowed(self) -> None:
        eq = build_equipment()
        eq.change_status(EquipmentStatus.RETIRED)
        assert eq.status == EquipmentStatus.RETIRED


class TestFullLifecycle:
    def test_assign_transfer_unassign(self) -> None:
        eq = build_equipment()
        eq.assign(10)
        assert eq.is_assigned

        prev = eq.transfer(20)
        assert prev == 10
        assert eq.assigned_to_employee_id == 20

        released = eq.unassign()
        assert released == 20
        assert not eq.is_assigned
        assert eq.status == EquipmentStatus.IN_STOCK

    def test_equipment_create_with_assigned_and_no_employee_raises(self) -> None:
        with pytest.raises(ValidationError, match="requires an employee"):
            Equipment.create(
                inventory_number=InventoryNumber("X-1"),
                name="Test",
                category_id=1,
                status=EquipmentStatus.ASSIGNED,
            )
