from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.domain.entities import Category, Equipment, EquipmentMovement
from app.domain.enums import EquipmentStatus, MovementType
from app.domain.value_objects import InventoryNumber
from app.presentation.api import app
from app.presentation.dependencies import get_category_service, get_equipment_service


# ─── STUBS ───────────────────────────────────────────────────────────────────

class StubCategoryService:
    async def list(self, *, skip: int = 0, limit: int = 100):
        cats = [
            _cat(1, "Laptops"),
            _cat(2, "Monitors"),
        ]
        return cats[skip : skip + limit], len(cats)

    async def get(self, category_id: int):
        if category_id == 1:
            return _cat(1, "Laptops")
        from app.domain.errors import NotFoundError
        raise NotFoundError(f"Category {category_id} was not found")

    async def create(self, command):
        return _cat(10, command.name)

    async def update(self, command):
        return _cat(command.category_id, command.name if command.name is not object() else "Laptops")

    async def delete(self, category_id: int):
        pass


class StubEquipmentService:
    async def assign(self, command):
        return _movement(1, command.equipment_id, MovementType.ASSIGN, None, command.employee_id)

    async def transfer(self, command):
        return _movement(2, command.equipment_id, MovementType.TRANSFER, 300, command.to_employee_id)

    async def unassign(self, command):
        return _movement(3, command.equipment_id, MovementType.UNASSIGN, 300, None)

    async def history(self, equipment_id: int):
        return [
            _movement(1, equipment_id, MovementType.ASSIGN, None, 300, comment="Issued"),
            _movement(2, equipment_id, MovementType.UNASSIGN, 300, None, comment="Returned"),
        ]

    async def list(self, filters):
        items = [_equipment(1), _equipment(2)]
        return items, len(items)

    async def get(self, equipment_id: int):
        if equipment_id == 1:
            return _equipment(1)
        from app.domain.errors import NotFoundError
        raise NotFoundError(f"Equipment {equipment_id} was not found")

    async def create(self, command):
        return _equipment(99)

    async def update(self, command):
        return _equipment(command.equipment_id)

    async def delete(self, equipment_id: int):
        pass


# ─── HELPERS ─────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _cat(cat_id: int, name: str) -> Category:
    cat = Category(id=cat_id, name=name, description=None, created_at=_now(), updated_at=_now())
    return cat


def _equipment(eq_id: int) -> Equipment:
    return Equipment(
        id=eq_id,
        inventory_number=InventoryNumber(f"EQ-{eq_id:03d}"),
        name=f"Equipment {eq_id}",
        category_id=1,
        status=EquipmentStatus.IN_STOCK,
        assigned_to_employee_id=None,
        serial_number=None,
        purchase_date=None,
        purchase_cost=None,
        notes=None,
        created_at=_now(),
        updated_at=_now(),
    )


def _movement(
    mov_id: int,
    equipment_id: int,
    movement_type: MovementType,
    from_emp: int | None,
    to_emp: int | None,
    comment: str | None = None,
) -> EquipmentMovement:
    now = _now()
    m = EquipmentMovement(
        id=mov_id,
        equipment_id=equipment_id,
        movement_type=movement_type,
        from_employee_id=from_emp,
        to_employee_id=to_emp,
        happened_at=now,
        comment=comment,
        created_at=now,
    )
    return m


# ─── FIXTURES ────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    app.dependency_overrides[get_equipment_service] = lambda: StubEquipmentService()
    app.dependency_overrides[get_category_service] = lambda: StubCategoryService()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ─── CATEGORY ENDPOINTS ───────────────────────────────────────────────────────

def test_list_categories(client: TestClient) -> None:
    response = client.get("/categories/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    assert payload["items"][0]["name"] == "Laptops"


def test_get_category(client: TestClient) -> None:
    response = client.get("/categories/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_category_not_found(client: TestClient) -> None:
    response = client.get("/categories/9999")
    assert response.status_code == 404
    assert response.json()["error_type"] == "not_found"


def test_create_category(client: TestClient) -> None:
    response = client.post("/categories/", json={"name": "Keyboards"})
    assert response.status_code == 201
    assert response.json()["name"] == "Keyboards"


def test_create_category_missing_name(client: TestClient) -> None:
    response = client.post("/categories/", json={})
    assert response.status_code == 422


def test_delete_category(client: TestClient) -> None:
    response = client.delete("/categories/1")
    assert response.status_code == 204


# ─── EQUIPMENT ENDPOINTS ──────────────────────────────────────────────────────

def test_list_equipment(client: TestClient) -> None:
    response = client.get("/equipment/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2


def test_get_equipment(client: TestClient) -> None:
    response = client.get("/equipment/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1


def test_get_equipment_not_found(client: TestClient) -> None:
    response = client.get("/equipment/9999")
    assert response.status_code == 404


def test_create_equipment(client: TestClient) -> None:
    payload = {
        "inventory_number": "LT-001",
        "name": "MacBook Pro",
        "category_id": 1,
    }
    response = client.post("/equipment/", json=payload)
    assert response.status_code == 201
    assert response.json()["id"] == 99


def test_create_equipment_missing_required_fields(client: TestClient) -> None:
    response = client.post("/equipment/", json={"name": "Missing inv and category"})
    assert response.status_code == 422


def test_delete_equipment(client: TestClient) -> None:
    response = client.delete("/equipment/1")
    assert response.status_code == 204


# ─── MOVEMENT ENDPOINTS ───────────────────────────────────────────────────────

def test_assign_endpoint_returns_movement(client: TestClient) -> None:
    response = client.post("/equipment/10/assign", json={"employee_id": 300, "comment": "Issued"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["equipment_id"] == 10
    assert payload["from_employee_id"] is None
    assert payload["to_employee_id"] == 300
    assert payload["movement_type"] == "assign"


def test_transfer_endpoint_returns_movement(client: TestClient) -> None:
    response = client.post("/equipment/10/transfer", json={"to_employee_id": 501, "comment": "Moved"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["from_employee_id"] == 300
    assert payload["to_employee_id"] == 501
    assert payload["movement_type"] == "transfer"


def test_unassign_endpoint_returns_movement(client: TestClient) -> None:
    response = client.post("/equipment/10/unassign", json={"comment": "Returned"})
    assert response.status_code == 201
    payload = response.json()
    assert payload["from_employee_id"] == 300
    assert payload["to_employee_id"] is None
    assert payload["movement_type"] == "unassign"


def test_history_endpoint_returns_movement_list(client: TestClient) -> None:
    response = client.get("/equipment/10/history")
    assert response.status_code == 200
    payload = response.json()
    assert payload["equipment_id"] == 10
    assert len(payload["movements"]) == 2
    assert payload["movements"][0]["movement_type"] == "assign"
    assert payload["movements"][1]["movement_type"] == "unassign"


def test_assign_missing_employee_id(client: TestClient) -> None:
    response = client.post("/equipment/10/assign", json={})
    assert response.status_code == 422


def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
