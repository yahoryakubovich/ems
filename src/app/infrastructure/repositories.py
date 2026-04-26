from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import CategoryRepository, EquipmentRepository, MovementRepository
from app.application.queries import EquipmentFilters
from app.domain.entities import Category, Equipment, EquipmentMovement
from app.domain.enums import EquipmentStatus, MovementType
from app.domain.value_objects import InventoryNumber, Money
from app.infrastructure.models import CategoryModel, EquipmentModel, EquipmentMovementModel


def _category_to_entity(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        name=model.name,
        description=model.description,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _equipment_to_entity(model: EquipmentModel) -> Equipment:
    money = None
    if model.purchase_cost_amount is not None and model.purchase_cost_currency is not None:
        money = Money(amount=model.purchase_cost_amount, currency=model.purchase_cost_currency)

    return Equipment(
        id=model.id,
        inventory_number=InventoryNumber(model.inventory_number),
        name=model.name,
        category_id=model.category_id,
        status=EquipmentStatus(model.status),
        assigned_to_employee_id=model.assigned_to_employee_id,
        serial_number=model.serial_number,
        purchase_date=model.purchase_date,
        purchase_cost=money,
        notes=model.notes,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _movement_to_entity(model: EquipmentMovementModel) -> EquipmentMovement:
    return EquipmentMovement(
        id=model.id,
        equipment_id=model.equipment_id,
        movement_type=MovementType(model.movement_type),
        from_employee_id=model.from_employee_id,
        to_employee_id=model.to_employee_id,
        happened_at=model.happened_at,
        comment=model.comment,
        created_at=model.created_at,
    )


class SqlAlchemyCategoryRepository(CategoryRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, category: Category) -> Category:
        model = None
        if category.id is not None:
            model = await self._session.get(CategoryModel, category.id)
        if model is None:
            model = CategoryModel()
            self._session.add(model)

        model.name = category.name
        model.description = category.description
        model.created_at = category.created_at
        model.updated_at = category.updated_at

        await self._session.flush()
        category.id = model.id
        return category

    async def get(self, category_id: int) -> Category | None:
        model = await self._session.get(CategoryModel, category_id)
        return _category_to_entity(model) if model is not None else None

    async def get_by_name(self, name: str) -> Category | None:
        result = await self._session.execute(select(CategoryModel).where(CategoryModel.name == name))
        model = result.scalar_one_or_none()
        return _category_to_entity(model) if model is not None else None

    async def list(self, *, skip: int, limit: int) -> tuple[list[Category], int]:
        total_result = await self._session.execute(select(func.count(CategoryModel.id)))
        total = total_result.scalar_one()
        result = await self._session.execute(
            select(CategoryModel).order_by(CategoryModel.name.asc()).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [_category_to_entity(model) for model in models], total

    async def delete(self, category_id: int) -> None:
        model = await self._session.get(CategoryModel, category_id)
        if model is not None:
            await self._session.delete(model)


class SqlAlchemyEquipmentRepository(EquipmentRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, equipment: Equipment) -> Equipment:
        model = None
        if equipment.id is not None:
            model = await self._session.get(EquipmentModel, equipment.id)
        if model is None:
            model = EquipmentModel()
            self._session.add(model)

        model.inventory_number = str(equipment.inventory_number)
        model.name = equipment.name
        model.category_id = equipment.category_id
        model.status = equipment.status.value
        model.assigned_to_employee_id = equipment.assigned_to_employee_id
        model.serial_number = equipment.serial_number
        model.purchase_date = equipment.purchase_date
        model.purchase_cost_amount = equipment.purchase_cost.amount if equipment.purchase_cost else None
        model.purchase_cost_currency = equipment.purchase_cost.currency if equipment.purchase_cost else None
        model.notes = equipment.notes
        model.created_at = equipment.created_at
        model.updated_at = equipment.updated_at

        await self._session.flush()
        equipment.id = model.id
        return equipment

    async def get(self, equipment_id: int) -> Equipment | None:
        model = await self._session.get(EquipmentModel, equipment_id)
        return _equipment_to_entity(model) if model is not None else None

    async def get_by_inventory_number(self, inventory_number: str) -> Equipment | None:
        result = await self._session.execute(
            select(EquipmentModel).where(EquipmentModel.inventory_number == inventory_number)
        )
        model = result.scalar_one_or_none()
        return _equipment_to_entity(model) if model is not None else None

    async def list(self, filters: EquipmentFilters) -> tuple[list[Equipment], int]:
        conditions = []
        if filters.category_id is not None:
            conditions.append(EquipmentModel.category_id == filters.category_id)
        if filters.assigned_to_employee_id is not None:
            conditions.append(EquipmentModel.assigned_to_employee_id == filters.assigned_to_employee_id)
        if filters.status is not None:
            conditions.append(EquipmentModel.status == filters.status.value)
        if filters.name is not None:
            conditions.append(EquipmentModel.name.ilike(f"%{filters.name.strip()}%"))
        if filters.inventory_number is not None:
            conditions.append(EquipmentModel.inventory_number.ilike(f"%{filters.inventory_number.strip().upper()}%"))
        if filters.purchase_date_from is not None:
            conditions.append(EquipmentModel.purchase_date >= filters.purchase_date_from)
        if filters.purchase_date_to is not None:
            conditions.append(EquipmentModel.purchase_date <= filters.purchase_date_to)

        query = select(EquipmentModel)
        count_query = select(func.count(EquipmentModel.id))
        for condition in conditions:
            query = query.where(condition)
            count_query = count_query.where(condition)

        total_result = await self._session.execute(count_query)
        total = total_result.scalar_one()
        result = await self._session.execute(
            query.order_by(EquipmentModel.created_at.desc()).offset(filters.skip).limit(filters.limit)
        )
        models = result.scalars().all()
        return [_equipment_to_entity(model) for model in models], total

    async def delete(self, equipment_id: int) -> None:
        model = await self._session.get(EquipmentModel, equipment_id)
        if model is not None:
            await self._session.delete(model)


class SqlAlchemyMovementRepository(MovementRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, movement: EquipmentMovement) -> EquipmentMovement:
        model = None
        if movement.id is not None:
            model = await self._session.get(EquipmentMovementModel, movement.id)
        if model is None:
            model = EquipmentMovementModel()
            self._session.add(model)

        model.equipment_id = movement.equipment_id
        model.movement_type = movement.movement_type.value
        model.from_employee_id = movement.from_employee_id
        model.to_employee_id = movement.to_employee_id
        model.happened_at = movement.happened_at
        model.comment = movement.comment
        model.created_at = movement.created_at

        await self._session.flush()
        movement.id = model.id
        return movement

    async def list_by_equipment(self, equipment_id: int) -> list[EquipmentMovement]:
        result = await self._session.execute(
            select(EquipmentMovementModel)
            .where(EquipmentMovementModel.equipment_id == equipment_id)
            .order_by(EquipmentMovementModel.happened_at.desc(), EquipmentMovementModel.id.desc())
        )
        return [_movement_to_entity(model) for model in result.scalars().all()]

    async def has_movements_for_equipment(self, equipment_id: int) -> bool:
        result = await self._session.execute(
            select(func.count(EquipmentMovementModel.id)).where(EquipmentMovementModel.equipment_id == equipment_id)
        )
        return bool(result.scalar_one())
