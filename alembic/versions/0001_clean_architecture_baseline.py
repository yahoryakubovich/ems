"""clean architecture baseline

Revision ID: 0001_clean_architecture_baseline
Revises:
Create Date: 2026-04-26 14:45:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0001_clean_architecture_baseline"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "equipments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("inventory_number", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_to_employee_id", sa.Integer(), nullable=True),
        sa.Column("serial_number", sa.String(length=255), nullable=True),
        sa.Column("purchase_date", sa.Date(), nullable=True),
        sa.Column("purchase_cost_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("purchase_cost_currency", sa.String(length=3), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("inventory_number"),
    )
    op.create_index("ix_equipments_category_id", "equipments", ["category_id"])
    op.create_index("ix_equipments_status", "equipments", ["status"])
    op.create_index("ix_equipments_assigned_to_employee_id", "equipments", ["assigned_to_employee_id"])

    op.create_table(
        "equipment_movements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("movement_type", sa.String(length=32), nullable=False),
        sa.Column("from_employee_id", sa.Integer(), nullable=True),
        sa.Column("to_employee_id", sa.Integer(), nullable=True),
        sa.Column("happened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipments.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_equipment_movements_equipment_id", "equipment_movements", ["equipment_id"])
    op.create_index("ix_equipment_movements_happened_at", "equipment_movements", ["happened_at"])


def downgrade() -> None:
    op.drop_index("ix_equipment_movements_happened_at", table_name="equipment_movements")
    op.drop_index("ix_equipment_movements_equipment_id", table_name="equipment_movements")
    op.drop_table("equipment_movements")

    op.drop_index("ix_equipments_assigned_to_employee_id", table_name="equipments")
    op.drop_index("ix_equipments_status", table_name="equipments")
    op.drop_index("ix_equipments_category_id", table_name="equipments")
    op.drop_table("equipments")

    op.drop_table("categories")
