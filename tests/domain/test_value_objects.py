from decimal import Decimal

import pytest

from app.domain.errors import ValidationError
from app.domain.value_objects import InventoryNumber, Money


class TestInventoryNumber:
    def test_normalizes_to_uppercase(self) -> None:
        inv = InventoryNumber("lt-001")
        assert inv.value == "LT-001"

    def test_strips_whitespace(self) -> None:
        inv = InventoryNumber("  LT-001  ")
        assert inv.value == "LT-001"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be empty"):
            InventoryNumber("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be empty"):
            InventoryNumber("   ")

    def test_str_returns_value(self) -> None:
        assert str(InventoryNumber("EQ-99")) == "EQ-99"

    def test_equality_is_value_based(self) -> None:
        assert InventoryNumber("EQ-1") == InventoryNumber("EQ-1")

    def test_immutable(self) -> None:
        inv = InventoryNumber("EQ-1")
        with pytest.raises(AttributeError):
            inv.value = "EQ-2"  # type: ignore[misc]


class TestMoney:
    def test_normalizes_currency_to_uppercase(self) -> None:
        m = Money(amount=Decimal("10.00"), currency="usd")
        assert m.currency == "USD"

    def test_quantizes_to_two_decimal_places(self) -> None:
        m = Money(amount=Decimal("9.999"), currency="USD")
        assert m.amount == Decimal("10.00")

    def test_rounds_half_up(self) -> None:
        m = Money(amount=Decimal("1.005"), currency="USD")
        assert m.amount == Decimal("1.01")

    def test_negative_amount_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be negative"):
            Money(amount=Decimal("-1.00"), currency="USD")

    def test_zero_amount_is_valid(self) -> None:
        m = Money(amount=Decimal("0"), currency="USD")
        assert m.amount == Decimal("0.00")

    def test_currency_must_be_3_letters(self) -> None:
        with pytest.raises(ValidationError, match="exactly 3 letters"):
            Money(amount=Decimal("1.00"), currency="US")

    def test_empty_currency_raises(self) -> None:
        with pytest.raises(ValidationError, match="cannot be empty"):
            Money(amount=Decimal("1.00"), currency="")

    def test_equality_is_value_based(self) -> None:
        a = Money(amount=Decimal("100.00"), currency="USD")
        b = Money(amount=Decimal("100.00"), currency="USD")
        assert a == b

    def test_different_currencies_are_not_equal(self) -> None:
        a = Money(amount=Decimal("100.00"), currency="USD")
        b = Money(amount=Decimal("100.00"), currency="EUR")
        assert a != b
