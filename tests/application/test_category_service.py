import pytest

from app.application.commands import CreateCategoryCommand, UpdateCategoryCommand
from app.application.services import CategoryService
from app.domain.entities import Category
from app.domain.errors import ConflictError, NotFoundError


@pytest.fixture
def service(uow_factory) -> CategoryService:
    return CategoryService(uow_factory)


async def test_create_category_success(service: CategoryService) -> None:
    result = await service.create(CreateCategoryCommand(name="Laptops"))
    assert result.id is not None
    assert result.name == "Laptops"


async def test_create_strips_name(service: CategoryService) -> None:
    result = await service.create(CreateCategoryCommand(name="  Monitors  "))
    assert result.name == "Monitors"


async def test_create_duplicate_name_raises(service: CategoryService) -> None:
    await service.create(CreateCategoryCommand(name="Phones"))
    with pytest.raises(ConflictError, match="already exists"):
        await service.create(CreateCategoryCommand(name="Phones"))


async def test_get_existing_category(service: CategoryService, seeded_category: Category) -> None:
    result = await service.get(1)
    assert result.name == "Laptops"


async def test_get_nonexistent_raises(service: CategoryService) -> None:
    with pytest.raises(NotFoundError):
        await service.get(9999)


async def test_list_categories(service: CategoryService) -> None:
    await service.create(CreateCategoryCommand(name="Cat A"))
    await service.create(CreateCategoryCommand(name="Cat B"))
    items, total = await service.list()
    assert total == 2
    assert len(items) == 2


async def test_update_renames_category(service: CategoryService, seeded_category: Category) -> None:
    result = await service.update(UpdateCategoryCommand(category_id=1, name="Workstations"))
    assert result.name == "Workstations"


async def test_update_to_duplicate_name_raises(
    service: CategoryService,
    seeded_category: Category,
    fake_categories,
) -> None:
    other = Category.create(name="Monitors")
    other.id = 2
    fake_categories._items[2] = other

    with pytest.raises(ConflictError, match="already exists"):
        await service.update(UpdateCategoryCommand(category_id=1, name="Monitors"))


async def test_update_nonexistent_category_raises(service: CategoryService) -> None:
    with pytest.raises(NotFoundError):
        await service.update(UpdateCategoryCommand(category_id=42, name="New"))


async def test_delete_empty_category(service: CategoryService, seeded_category: Category) -> None:
    await service.delete(1)
    with pytest.raises(NotFoundError):
        await service.get(1)


async def test_delete_nonexistent_category_raises(service: CategoryService) -> None:
    with pytest.raises(NotFoundError):
        await service.delete(99)


async def test_delete_category_with_equipment_raises(
    service: CategoryService,
    seeded_category: Category,
    seeded_equipment,
) -> None:
    with pytest.raises(ConflictError, match="used by equipment"):
        await service.delete(1)
