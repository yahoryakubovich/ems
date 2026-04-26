from enum import StrEnum


class EquipmentStatus(StrEnum):
    IN_STOCK = "in_stock"
    ASSIGNED = "assigned"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class MovementType(StrEnum):
    ASSIGN = "assign"
    TRANSFER = "transfer"
    UNASSIGN = "unassign"
