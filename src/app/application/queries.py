from dataclasses import dataclass
from datetime import date

from app.domain.enums import EquipmentStatus


@dataclass(frozen=True, slots=True)
class EquipmentFilters:
    category_id: int | None = None
    assigned_to_employee_id: int | None = None
    status: EquipmentStatus | None = None
    name: str | None = None
    inventory_number: str | None = None
    purchase_date_from: date | None = None
    purchase_date_to: date | None = None
    skip: int = 0
    limit: int = 100
