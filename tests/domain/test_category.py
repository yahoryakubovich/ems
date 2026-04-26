import time

import pytest

from app.domain.entities import Category
from app.domain.errors import ValidationError


def build_category(name: str = "Laptops") -> Category:
    return Category.create(name=name)


class TestCategoryCreate:
    def test_strips_name(self) -> None:
        cat = Category.create(name="  Monitors  ")
        assert cat.name == "Monitors"

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be empty"):
            Category.create(name="")

    def test_whitespace_only_name_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be empty"):
            Category.create(name="   ")

    def test_id_is_none_on_creation(self) -> None:
        cat = Category.create(name="Phones")
        assert cat.id is None

    def test_description_is_stripped(self) -> None:
        cat = Category.create(name="Phones", description="  Corporate phones  ")
        assert cat.description == "Corporate phones"

    def test_empty_description_becomes_none(self) -> None:
        cat = Category.create(name="Phones", description="   ")
        assert cat.description is None

    def test_created_at_equals_updated_at_on_creation(self) -> None:
        cat = Category.create(name="Phones")
        assert cat.created_at == cat.updated_at


class TestCategoryRename:
    def test_rename_updates_name(self) -> None:
        cat = build_category("Old")
        cat.rename("New")
        assert cat.name == "New"

    def test_rename_empty_raises(self) -> None:
        cat = build_category()
        with pytest.raises(ValidationError):
            cat.rename("")

    def test_rename_updates_updated_at(self) -> None:
        cat = build_category()
        before = cat.updated_at
        time.sleep(0.01)
        cat.rename("Updated")
        assert cat.updated_at > before

    def test_update_description_to_none(self) -> None:
        cat = Category.create(name="X", description="Some desc")
        cat.update_description(None)
        assert cat.description is None
