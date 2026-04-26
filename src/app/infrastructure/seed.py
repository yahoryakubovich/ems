from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import date

from sqlalchemy import delete, select, func

from app.application.commands import (
    AssignEquipmentCommand,
    CreateCategoryCommand,
    CreateEquipmentCommand,
    TransferEquipmentCommand,
    UnassignEquipmentCommand,
    UpdateEquipmentCommand,
)
from app.application.services import CategoryService, EquipmentService
from app.domain.enums import EquipmentStatus
from app.infrastructure.database import SessionFactory
from app.infrastructure.models import CategoryModel, EquipmentModel, EquipmentMovementModel
from app.infrastructure.uow import SqlAlchemyUnitOfWork


@dataclass(frozen=True, slots=True)
class DemoCategory:
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class DemoEquipment:
    inventory_number: str
    name: str
    category_name: str
    serial_number: str
    purchase_date: date
    purchase_cost_amount: float
    purchase_cost_currency: str
    notes: str
    status: EquipmentStatus = EquipmentStatus.IN_STOCK


DEMO_CATEGORIES = [
    DemoCategory("Laptops", "Portable workstations"),
    DemoCategory("Monitors", "External displays"),
    DemoCategory("Phones", "Corporate mobile devices"),
    DemoCategory("Accessories", "Peripheral and desk equipment"),
]


DEMO_EQUIPMENTS = [
    DemoEquipment(
        inventory_number="LT-001",
        name="MacBook Pro 14",
        category_name="Laptops",
        serial_number="MBP14-001",
        purchase_date=date(2025, 1, 15),
        purchase_cost_amount=2499.99,
        purchase_cost_currency="USD",
        notes="Design team laptop",
    ),
    DemoEquipment(
        inventory_number="LT-002",
        name='ThinkPad X1 Carbon',
        category_name="Laptops",
        serial_number="TPX1-002",
        purchase_date=date(2025, 2, 5),
        purchase_cost_amount=2199.00,
        purchase_cost_currency="USD",
        notes="Engineering lead laptop",
    ),
    DemoEquipment(
        inventory_number="MN-001",
        name="Dell UltraSharp 27",
        category_name="Monitors",
        serial_number="DU27-001",
        purchase_date=date(2025, 3, 12),
        purchase_cost_amount=489.50,
        purchase_cost_currency="USD",
        notes="Open office monitor",
        status=EquipmentStatus.MAINTENANCE,
    ),
    DemoEquipment(
        inventory_number="PH-001",
        name="iPhone 15",
        category_name="Phones",
        serial_number="IP15-001",
        purchase_date=date(2025, 4, 2),
        purchase_cost_amount=1099.00,
        purchase_cost_currency="USD",
        notes="Sales department phone",
    ),
    DemoEquipment(
        inventory_number="AC-001",
        name="Logitech MX Keys",
        category_name="Accessories",
        serial_number="MXK-001",
        purchase_date=date(2025, 5, 20),
        purchase_cost_amount=129.99,
        purchase_cost_currency="USD",
        notes="Spare keyboard",
        status=EquipmentStatus.RETIRED,
    ),
]


async def reset_demo_data() -> None:
    async with SessionFactory() as session:
        await session.execute(delete(EquipmentMovementModel))
        await session.execute(delete(EquipmentModel))
        await session.execute(delete(CategoryModel))
        await session.commit()


async def database_has_data() -> bool:
    async with SessionFactory() as session:
        result = await session.execute(select(func.count(CategoryModel.id)))
        return bool(result.scalar_one())


async def seed_demo_data(*, reset: bool = False) -> None:
    if reset:
        await reset_demo_data()
    elif await database_has_data():
        print("Database already contains data. Run with --reset to recreate demo content.")
        return

    category_service = CategoryService(SqlAlchemyUnitOfWork)
    equipment_service = EquipmentService(SqlAlchemyUnitOfWork)

    categories_by_name: dict[str, int] = {}
    for item in DEMO_CATEGORIES:
        category = await category_service.create(
            CreateCategoryCommand(name=item.name, description=item.description)
        )
        categories_by_name[item.name] = category.id or 0

    created_equipment: dict[str, int] = {}
    for item in DEMO_EQUIPMENTS:
        equipment = await equipment_service.create(
            CreateEquipmentCommand(
                inventory_number=item.inventory_number,
                name=item.name,
                category_id=categories_by_name[item.category_name],
                serial_number=item.serial_number,
                purchase_date=item.purchase_date,
                purchase_cost_amount=item.purchase_cost_amount,
                purchase_cost_currency=item.purchase_cost_currency,
                notes=item.notes,
                status=item.status,
            )
        )
        created_equipment[item.inventory_number] = equipment.id or 0

    await equipment_service.assign(
        AssignEquipmentCommand(
            equipment_id=created_equipment["LT-001"],
            employee_id=101,
            comment="Issued to designer",
        )
    )
    await equipment_service.assign(
        AssignEquipmentCommand(
            equipment_id=created_equipment["LT-002"],
            employee_id=205,
            comment="Issued to engineering lead",
        )
    )
    await equipment_service.transfer(
        TransferEquipmentCommand(
            equipment_id=created_equipment["LT-002"],
            to_employee_id=206,
            comment="Transferred to acting engineering lead",
        )
    )
    await equipment_service.assign(
        AssignEquipmentCommand(
            equipment_id=created_equipment["PH-001"],
            employee_id=301,
            comment="Issued to sales representative",
        )
    )
    await equipment_service.unassign(
        UnassignEquipmentCommand(
            equipment_id=created_equipment["PH-001"],
            comment="Returned after replacement",
        )
    )
    await equipment_service.update(
        UpdateEquipmentCommand(
            equipment_id=created_equipment["MN-001"],
            notes="Sent to service center for diagnostics",
        )
    )

    print("Demo data created successfully.")
    print("Categories:", ", ".join(categories_by_name))
    print("Equipment count:", len(created_equipment))


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data for EMS")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing categories, equipment, and movements before seeding",
    )
    args = parser.parse_args()
    asyncio.run(seed_demo_data(reset=args.reset))


if __name__ == "__main__":
    main()
