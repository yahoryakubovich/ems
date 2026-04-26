from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.domain.errors import ValidationError


def _normalize_text(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{field_name} cannot be empty")
    return normalized


@dataclass(frozen=True, slots=True)
class InventoryNumber:
    value: str

    def __post_init__(self) -> None:
        normalized = _normalize_text(self.value, field_name="Inventory number").upper()
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, Decimal):
            amount = self.amount
        else:
            amount = Decimal(str(self.amount))

        if amount < 0:
            raise ValidationError("Purchase cost cannot be negative")

        currency = _normalize_text(self.currency, field_name="Currency").upper()
        if len(currency) != 3:
            raise ValidationError("Currency must contain exactly 3 letters")

        object.__setattr__(self, "amount", amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        object.__setattr__(self, "currency", currency)
