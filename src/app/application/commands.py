from dataclasses import dataclass
from datetime import date, datetime

from app.domain.enums import EquipmentStatus

UNSET = object()


@dataclass(frozen=True, slots=True)
class CreateCategoryCommand:
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateCategoryCommand:
    category_id: int
    name: object = UNSET
    description: object = UNSET


@dataclass(frozen=True, slots=True)
class CreateEquipmentCommand:
    inventory_number: str
    name: str
    category_id: int
    serial_number: str | None = None
    purchase_date: date | None = None
    purchase_cost_amount: float | None = None
    purchase_cost_currency: str | None = None
    notes: str | None = None
    status: EquipmentStatus = EquipmentStatus.IN_STOCK


@dataclass(frozen=True, slots=True)
class UpdateEquipmentCommand:
    equipment_id: int
    name: object = UNSET
    category_id: object = UNSET
    serial_number: object = UNSET
    purchase_date: object = UNSET
    purchase_cost_amount: object = UNSET
    purchase_cost_currency: object = UNSET
    notes: object = UNSET
    status: object = UNSET


@dataclass(frozen=True, slots=True)
class AssignEquipmentCommand:
    equipment_id: int
    employee_id: int
    comment: str | None = None
    happened_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TransferEquipmentCommand:
    equipment_id: int
    to_employee_id: int
    comment: str | None = None
    happened_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class UnassignEquipmentCommand:
    equipment_id: int
    comment: str | None = None
    happened_at: datetime | None = None
