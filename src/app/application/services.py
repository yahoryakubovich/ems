from __future__ import annotations

from decimal import Decimal

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
from app.application.ports import UnitOfWork
from app.application.queries import EquipmentFilters
from app.domain.entities import Category, Equipment, EquipmentMovement
from app.domain.enums import EquipmentStatus, MovementType
from app.domain.errors import ConflictError, NotFoundError
from app.domain.value_objects import InventoryNumber, Money


def _money_from_fields(amount: float | None, currency: str | None) -> Money | None:
    if amount is None:
        return None
    return Money(amount=Decimal(str(amount)), currency=currency or "USD")


class CategoryService:
    def __init__(self, uow_factory):
        self._uow_factory = uow_factory

    async def create(self, command: CreateCategoryCommand) -> Category:
        async with self._uow_factory() as uow:
            existing = await uow.categories.get_by_name(command.name.strip())
            if existing is not None:
                raise ConflictError(f'Category "{command.name}" already exists')

            category = Category.create(name=command.name, description=command.description)
            return await uow.categories.add(category)

    async def get(self, category_id: int) -> Category:
        async with self._uow_factory() as uow:
            category = await uow.categories.get(category_id)
            if category is None:
                raise NotFoundError(f"Category {category_id} was not found")
            return category

    async def list(self, *, skip: int = 0, limit: int = 100) -> tuple[list[Category], int]:
        async with self._uow_factory() as uow:
            return await uow.categories.list(skip=skip, limit=limit)

    async def update(self, command: UpdateCategoryCommand) -> Category:
        async with self._uow_factory() as uow:
            category = await uow.categories.get(command.category_id)
            if category is None:
                raise NotFoundError(f"Category {command.category_id} was not found")

            if command.name is not UNSET:
                existing = await uow.categories.get_by_name(str(command.name).strip())
                if existing is not None and existing.id != category.id:
                    raise ConflictError(f'Category "{command.name}" already exists')
                category.rename(str(command.name))

            if command.description is not UNSET:
                category.update_description(command.description)

            return await uow.categories.add(category)

    async def delete(self, category_id: int) -> None:
        async with self._uow_factory() as uow:
            category = await uow.categories.get(category_id)
            if category is None:
                raise NotFoundError(f"Category {category_id} was not found")

            equipments, total = await uow.equipments.list(
                EquipmentFilters(category_id=category_id, skip=0, limit=1)
            )
            if total > 0 or equipments:
                raise ConflictError("Cannot delete a category that is used by equipment")

            await uow.categories.delete(category_id)


class EquipmentService:
    def __init__(self, uow_factory):
        self._uow_factory = uow_factory

    async def create(self, command: CreateEquipmentCommand) -> Equipment:
        async with self._uow_factory() as uow:
            await self._ensure_category_exists(uow, command.category_id)
            await self._ensure_inventory_number_is_unique(uow, command.inventory_number)

            equipment = Equipment.create(
                inventory_number=InventoryNumber(command.inventory_number),
                name=command.name,
                category_id=command.category_id,
                serial_number=command.serial_number,
                purchase_date=command.purchase_date,
                purchase_cost=_money_from_fields(command.purchase_cost_amount, command.purchase_cost_currency),
                notes=command.notes,
                status=command.status,
            )
            return await uow.equipments.add(equipment)

    async def get(self, equipment_id: int) -> Equipment:
        async with self._uow_factory() as uow:
            equipment = await uow.equipments.get(equipment_id)
            if equipment is None:
                raise NotFoundError(f"Equipment {equipment_id} was not found")
            return equipment

    async def list(self, filters: EquipmentFilters) -> tuple[list[Equipment], int]:
        async with self._uow_factory() as uow:
            return await uow.equipments.list(filters)

    async def update(self, command: UpdateEquipmentCommand) -> Equipment:
        async with self._uow_factory() as uow:
            equipment = await self._get_required_equipment(uow, command.equipment_id)

            if command.category_id is not UNSET:
                await self._ensure_category_exists(uow, command.category_id)

            if command.name is not UNSET:
                equipment.set_name(command.name)
            if command.category_id is not UNSET:
                equipment.set_category(command.category_id)
            if command.serial_number is not UNSET:
                equipment.set_serial_number(command.serial_number)
            if command.purchase_date is not UNSET:
                equipment.set_purchase_date(command.purchase_date)
            if command.notes is not UNSET:
                equipment.set_notes(command.notes)
            if command.status is not UNSET:
                equipment.change_status(command.status)
            if command.purchase_cost_amount is not UNSET or command.purchase_cost_currency is not UNSET:
                if command.purchase_cost_amount is None:
                    equipment.set_purchase_cost(None)
                elif command.purchase_cost_amount is not UNSET:
                    currency = (
                        command.purchase_cost_currency
                        if command.purchase_cost_currency is not UNSET
                        else (equipment.purchase_cost.currency if equipment.purchase_cost else "USD")
                    )
                    equipment.set_purchase_cost(_money_from_fields(command.purchase_cost_amount, currency))
                elif equipment.purchase_cost is not None:
                    equipment.set_purchase_cost(
                        _money_from_fields(equipment.purchase_cost.amount, command.purchase_cost_currency)
                    )

            equipment.touch()
            return await uow.equipments.add(equipment)

    async def delete(self, equipment_id: int) -> None:
        async with self._uow_factory() as uow:
            equipment = await self._get_required_equipment(uow, equipment_id)
            if equipment.is_assigned:
                raise ConflictError("Assigned equipment cannot be deleted")
            if await uow.movements.has_movements_for_equipment(equipment_id):
                raise ConflictError("Equipment with movement history cannot be deleted")
            await uow.equipments.delete(equipment_id)

    async def assign(self, command: AssignEquipmentCommand) -> EquipmentMovement:
        async with self._uow_factory() as uow:
            equipment = await self._get_required_equipment(uow, command.equipment_id)
            equipment.assign(command.employee_id)
            equipment = await uow.equipments.add(equipment)
            movement = EquipmentMovement.create(
                equipment_id=equipment.id or command.equipment_id,
                movement_type=MovementType.ASSIGN,
                from_employee_id=None,
                to_employee_id=command.employee_id,
                happened_at=command.happened_at,
                comment=command.comment,
            )
            return await uow.movements.add(movement)

    async def transfer(self, command: TransferEquipmentCommand) -> EquipmentMovement:
        async with self._uow_factory() as uow:
            equipment = await self._get_required_equipment(uow, command.equipment_id)
            previous_employee_id = equipment.transfer(command.to_employee_id)
            equipment = await uow.equipments.add(equipment)
            movement = EquipmentMovement.create(
                equipment_id=equipment.id or command.equipment_id,
                movement_type=MovementType.TRANSFER,
                from_employee_id=previous_employee_id,
                to_employee_id=command.to_employee_id,
                happened_at=command.happened_at,
                comment=command.comment,
            )
            return await uow.movements.add(movement)

    async def unassign(self, command: UnassignEquipmentCommand) -> EquipmentMovement:
        async with self._uow_factory() as uow:
            equipment = await self._get_required_equipment(uow, command.equipment_id)
            previous_employee_id = equipment.unassign()
            equipment = await uow.equipments.add(equipment)
            movement = EquipmentMovement.create(
                equipment_id=equipment.id or command.equipment_id,
                movement_type=MovementType.UNASSIGN,
                from_employee_id=previous_employee_id,
                to_employee_id=None,
                happened_at=command.happened_at,
                comment=command.comment,
            )
            return await uow.movements.add(movement)

    async def history(self, equipment_id: int) -> list[EquipmentMovement]:
        async with self._uow_factory() as uow:
            await self._get_required_equipment(uow, equipment_id)
            return await uow.movements.list_by_equipment(equipment_id)

    async def _ensure_category_exists(self, uow: UnitOfWork, category_id: int) -> None:
        category = await uow.categories.get(category_id)
        if category is None:
            raise NotFoundError(f"Category {category_id} was not found")

    async def _ensure_inventory_number_is_unique(self, uow: UnitOfWork, inventory_number: str) -> None:
        existing = await uow.equipments.get_by_inventory_number(inventory_number.strip().upper())
        if existing is not None:
            raise ConflictError(f'Equipment with inventory number "{inventory_number}" already exists')

    async def _get_required_equipment(self, uow: UnitOfWork, equipment_id: int) -> Equipment:
        equipment = await uow.equipments.get(equipment_id)
        if equipment is None:
            raise NotFoundError(f"Equipment {equipment_id} was not found")
        return equipment


