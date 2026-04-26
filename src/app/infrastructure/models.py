from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CategoryModel(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    equipments = relationship("EquipmentModel", back_populates="category")


class EquipmentModel(Base):
    __tablename__ = "equipments"
    __table_args__ = (
        Index("ix_equipments_category_id", "category_id"),
        Index("ix_equipments_status", "status"),
        Index("ix_equipments_assigned_to_employee_id", "assigned_to_employee_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inventory_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    assigned_to_employee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purchase_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    purchase_cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    purchase_cost_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    category = relationship("CategoryModel", back_populates="equipments")
    movements = relationship("EquipmentMovementModel", back_populates="equipment")


class EquipmentMovementModel(Base):
    __tablename__ = "equipment_movements"
    __table_args__ = (
        Index("ix_equipment_movements_equipment_id", "equipment_id"),
        Index("ix_equipment_movements_happened_at", "happened_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipments.id", ondelete="CASCADE"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(32), nullable=False)
    from_employee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    to_employee_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    equipment = relationship("EquipmentModel", back_populates="movements")
