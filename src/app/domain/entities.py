from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from app.domain.enums import EquipmentStatus, MovementType
from app.domain.errors import BusinessRuleViolation, ValidationError
from app.domain.value_objects import InventoryNumber, Money


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@dataclass(slots=True)
class Category:
    id: int | None
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls, *, name: str, description: str | None = None) -> Category:
        now = utc_now()
        return cls(
            id=None,
            name=cls._validate_name(name),
            description=_normalize_optional_text(description),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise ValidationError("Category name cannot be empty")
        return normalized

    def rename(self, name: str) -> None:
        self.name = self._validate_name(name)
        self.touch()

    def update_description(self, description: str | None) -> None:
        self.description = _normalize_optional_text(description)
        self.touch()

    def touch(self) -> None:
        self.updated_at = utc_now()


@dataclass(slots=True)
class Equipment:
    id: int | None
    inventory_number: InventoryNumber
    name: str
    category_id: int
    status: EquipmentStatus
    assigned_to_employee_id: int | None
    serial_number: str | None
    purchase_date: date | None
    purchase_cost: Money | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        inventory_number: InventoryNumber,
        name: str,
        category_id: int,
        serial_number: str | None = None,
        purchase_date: date | None = None,
        purchase_cost: Money | None = None,
        notes: str | None = None,
        status: EquipmentStatus = EquipmentStatus.IN_STOCK,
        assigned_to_employee_id: int | None = None,
    ) -> Equipment:
        now = utc_now()
        equipment = cls(
            id=None,
            inventory_number=inventory_number,
            name=cls._validate_name(name),
            category_id=cls._validate_category_id(category_id),
            status=status,
            assigned_to_employee_id=assigned_to_employee_id,
            serial_number=_normalize_optional_text(serial_number),
            purchase_date=purchase_date,
            purchase_cost=purchase_cost,
            notes=_normalize_optional_text(notes),
            created_at=now,
            updated_at=now,
        )
        equipment._validate_assignment_state()
        return equipment

    @staticmethod
    def _validate_name(name: str) -> str:
        normalized = name.strip()
        if not normalized:
            raise ValidationError("Equipment name cannot be empty")
        return normalized

    @staticmethod
    def _validate_category_id(category_id: int) -> int:
        if category_id <= 0:
            raise ValidationError("Category ID must be positive")
        return category_id

    @staticmethod
    def _validate_employee_id(employee_id: int) -> int:
        if employee_id <= 0:
            raise ValidationError("Employee ID must be positive")
        return employee_id

    def _validate_assignment_state(self) -> None:
        if self.assigned_to_employee_id is not None and self.status != EquipmentStatus.ASSIGNED:
            raise ValidationError("Assigned equipment must have status 'assigned'")
        if self.assigned_to_employee_id is None and self.status == EquipmentStatus.ASSIGNED:
            raise ValidationError("Status 'assigned' requires an employee assignment")
        if self.assigned_to_employee_id is not None:
            self._validate_employee_id(self.assigned_to_employee_id)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def set_name(self, name: str) -> None:
        self.name = self._validate_name(name)

    def set_category(self, category_id: int) -> None:
        self.category_id = self._validate_category_id(category_id)

    def set_serial_number(self, serial_number: str | None) -> None:
        self.serial_number = _normalize_optional_text(serial_number)

    def set_purchase_date(self, purchase_date: date | None) -> None:
        self.purchase_date = purchase_date

    def set_purchase_cost(self, purchase_cost: Money | None) -> None:
        self.purchase_cost = purchase_cost

    def set_notes(self, notes: str | None) -> None:
        self.notes = _normalize_optional_text(notes)

    def change_status(self, new_status: EquipmentStatus) -> None:
        if new_status == EquipmentStatus.ASSIGNED:
            raise BusinessRuleViolation("Use assign or transfer operations to set assigned status")
        if self.assigned_to_employee_id is not None:
            raise BusinessRuleViolation("Cannot change status while equipment is assigned")
        if self.status == EquipmentStatus.RETIRED and new_status != EquipmentStatus.RETIRED:
            raise BusinessRuleViolation("Retired equipment cannot return to an active lifecycle")
        self.status = new_status

    def assign(self, employee_id: int) -> None:
        employee_id = self._validate_employee_id(employee_id)
        if self.status == EquipmentStatus.RETIRED:
            raise BusinessRuleViolation("Retired equipment cannot be assigned")
        if self.status == EquipmentStatus.MAINTENANCE:
            raise BusinessRuleViolation("Equipment in maintenance cannot be assigned")
        if self.assigned_to_employee_id is not None:
            raise BusinessRuleViolation("Equipment is already assigned; use transfer instead")

        self.assigned_to_employee_id = employee_id
        self.status = EquipmentStatus.ASSIGNED
        self.touch()

    def transfer(self, employee_id: int) -> int:
        employee_id = self._validate_employee_id(employee_id)
        if self.assigned_to_employee_id is None:
            raise BusinessRuleViolation("Cannot transfer equipment that is not assigned")
        if self.assigned_to_employee_id == employee_id:
            raise BusinessRuleViolation("Equipment is already assigned to this employee")

        previous_employee_id = self.assigned_to_employee_id
        self.assigned_to_employee_id = employee_id
        self.status = EquipmentStatus.ASSIGNED
        self.touch()
        return previous_employee_id

    def unassign(self) -> int:
        if self.assigned_to_employee_id is None:
            raise BusinessRuleViolation("Equipment is not assigned")

        previous_employee_id = self.assigned_to_employee_id
        self.assigned_to_employee_id = None
        self.status = EquipmentStatus.IN_STOCK
        self.touch()
        return previous_employee_id

    @property
    def is_assigned(self) -> bool:
        return self.assigned_to_employee_id is not None


@dataclass(slots=True)
class EquipmentMovement:
    id: int | None
    equipment_id: int
    movement_type: MovementType
    from_employee_id: int | None
    to_employee_id: int | None
    happened_at: datetime
    comment: str | None
    created_at: datetime

    @classmethod
    def create(
        cls,
        *,
        equipment_id: int,
        movement_type: MovementType,
        from_employee_id: int | None,
        to_employee_id: int | None,
        happened_at: datetime | None = None,
        comment: str | None = None,
    ) -> EquipmentMovement:
        if equipment_id <= 0:
            raise ValidationError("Equipment ID must be positive")
        if from_employee_id is None and to_employee_id is None:
            raise ValidationError("Movement must contain at least one employee")
        if from_employee_id is not None and from_employee_id <= 0:
            raise ValidationError("Source employee ID must be positive")
        if to_employee_id is not None and to_employee_id <= 0:
            raise ValidationError("Destination employee ID must be positive")
        if from_employee_id is not None and to_employee_id is not None and from_employee_id == to_employee_id:
            raise ValidationError("Source and destination employees must be different")

        now = utc_now()
        return cls(
            id=None,
            equipment_id=equipment_id,
            movement_type=movement_type,
            from_employee_id=from_employee_id,
            to_employee_id=to_employee_id,
            happened_at=happened_at or now,
            comment=_normalize_optional_text(comment),
            created_at=now,
        )
