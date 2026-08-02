from dataclasses import dataclass

from app.core.config import get_settings


def line_total_vnd(unit_price_vnd: int, quantity: int) -> int:
    return unit_price_vnd * quantity


def shipping_fee_vnd(subtotal_vnd: int) -> int:
    settings = get_settings()
    if subtotal_vnd >= settings.free_shipping_threshold_vnd:
        return 0
    return settings.shipping_flat_fee_vnd


@dataclass(frozen=True)
class AmountBreakdown:
    subtotal_vnd: int
    discount_amount_vnd: int
    shipping_fee_vnd: int
    total_vnd: int


def compute_amounts(
    line_totals: list[int], discount_amount_vnd: int = 0
) -> AmountBreakdown:
    subtotal = sum(line_totals)
    if discount_amount_vnd < 0 or discount_amount_vnd > subtotal:
        raise ValueError("discount_amount_vnd must be between zero and subtotal")
    shipping = shipping_fee_vnd(subtotal)
    return AmountBreakdown(
        subtotal_vnd=subtotal,
        discount_amount_vnd=discount_amount_vnd,
        shipping_fee_vnd=shipping,
        total_vnd=subtotal - discount_amount_vnd + shipping,
    )
