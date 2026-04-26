from datetime import date, datetime

from pydantic import BaseModel, Field

from app.application.commands import (
    AssignEquipmentCommand,
    CreateCategoryCommand,
    CreateEquipmentCommand,
    TransferEquipmentCommand,
    UNSET,
    UnassignEquipmentCommand,
    UpdateCategoryCommand,
    UpdateEquipmentCommand,
)
from app.domain.entities import Category, Equipment, EquipmentMovement
from app.domain.enums import EquipmentStatus, MovementType


class CategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: str | None = None

    def to_command(self) -> CreateCategoryCommand:
        return CreateCategoryCommand(name=self.name, description=self.description)


class CategoryUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1)
    description: str | None = None

    def to_command(self, category_id: int) -> UpdateCategoryCommand:
        payload = self.model_dump(exclude_unset=True)
        return UpdateCategoryCommand(
            category_id=category_id,
            name=payload.get("name", UNSET),
            description=payload.get("description", UNSET),
        )


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, category: Category) -> "CategoryResponse":
        return cls.model_validate(category, from_attributes=True)


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
    offset: int
    limit: int


class MoneyResponse(BaseModel):
    amount: str
    currency: str


class EquipmentCreateRequest(BaseModel):
    inventory_number: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    category_id: int = Field(..., gt=0)
    serial_number: str | None = None
    purchase_date: date | None = None
    purchase_cost_amount: float | None = Field(None, ge=0)
    purchase_cost_currency: str | None = None
    notes: str | None = None
    status: EquipmentStatus = EquipmentStatus.IN_STOCK

    def to_command(self) -> CreateEquipmentCommand:
        return CreateEquipmentCommand(**self.model_dump())


class EquipmentUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1)
    category_id: int | None = Field(None, gt=0)
    serial_number: str | None = None
    purchase_date: date | None = None
    purchase_cost_amount: float | None = Field(None, ge=0)
    purchase_cost_currency: str | None = None
    notes: str | None = None
    status: EquipmentStatus | None = None

    def to_command(self, equipment_id: int) -> UpdateEquipmentCommand:
        payload = self.model_dump(exclude_unset=True)
        return UpdateEquipmentCommand(
            equipment_id=equipment_id,
            name=payload.get("name", UNSET),
            category_id=payload.get("category_id", UNSET),
            serial_number=payload.get("serial_number", UNSET),
            purchase_date=payload.get("purchase_date", UNSET),
            purchase_cost_amount=payload.get("purchase_cost_amount", UNSET),
            purchase_cost_currency=payload.get("purchase_cost_currency", UNSET),
            notes=payload.get("notes", UNSET),
            status=payload.get("status", UNSET),
        )


class EquipmentResponse(BaseModel):
    id: int
    inventory_number: str
    name: str
    category_id: int
    status: EquipmentStatus
    assigned_to_employee_id: int | None
    serial_number: str | None
    purchase_date: date | None
    purchase_cost: MoneyResponse | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, equipment: Equipment) -> "EquipmentResponse":
        return cls(
            id=equipment.id or 0,
            inventory_number=str(equipment.inventory_number),
            name=equipment.name,
            category_id=equipment.category_id,
            status=equipment.status,
            assigned_to_employee_id=equipment.assigned_to_employee_id,
            serial_number=equipment.serial_number,
            purchase_date=equipment.purchase_date,
            purchase_cost=(
                MoneyResponse(amount=str(equipment.purchase_cost.amount), currency=equipment.purchase_cost.currency)
                if equipment.purchase_cost
                else None
            ),
            notes=equipment.notes,
            created_at=equipment.created_at,
            updated_at=equipment.updated_at,
        )


class EquipmentListResponse(BaseModel):
    items: list[EquipmentResponse]
    total: int
    offset: int
    limit: int


class EquipmentAssignmentRequest(BaseModel):
    employee_id: int = Field(..., gt=0)
    comment: str | None = None

    def to_command(self, equipment_id: int) -> AssignEquipmentCommand:
        return AssignEquipmentCommand(equipment_id=equipment_id, employee_id=self.employee_id, comment=self.comment)


class EquipmentTransferRequest(BaseModel):
    to_employee_id: int = Field(..., gt=0)
    comment: str | None = None

    def to_command(self, equipment_id: int) -> TransferEquipmentCommand:
        return TransferEquipmentCommand(
            equipment_id=equipment_id,
            to_employee_id=self.to_employee_id,
            comment=self.comment,
        )


class EquipmentUnassignRequest(BaseModel):
    comment: str | None = None

    def to_command(self, equipment_id: int) -> UnassignEquipmentCommand:
        return UnassignEquipmentCommand(equipment_id=equipment_id, comment=self.comment)


class EquipmentMovementResponse(BaseModel):
    id: int
    equipment_id: int
    movement_type: MovementType
    from_employee_id: int | None
    to_employee_id: int | None
    happened_at: datetime
    comment: str | None
    created_at: datetime

    @classmethod
    def from_entity(cls, movement: EquipmentMovement) -> "EquipmentMovementResponse":
        return cls.model_validate(movement, from_attributes=True)


class EquipmentHistoryResponse(BaseModel):
    equipment_id: int
    movements: list[EquipmentMovementResponse]
