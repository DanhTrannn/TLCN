from app.common.money import compute_amounts, line_total_vnd, shipping_fee_vnd
from app.core.config import get_settings


def test_line_total_exact_integer():
    assert line_total_vnd(149000, 3) == 447000


def test_shipping_free_above_threshold():
    settings = get_settings()
    assert shipping_fee_vnd(settings.free_shipping_threshold_vnd) == 0
    assert shipping_fee_vnd(settings.free_shipping_threshold_vnd + 1) == 0


def test_shipping_flat_below_threshold():
    settings = get_settings()
    assert shipping_fee_vnd(settings.free_shipping_threshold_vnd - 1) == settings.shipping_flat_fee_vnd


def test_compute_amounts_totals():
    settings = get_settings()
    breakdown = compute_amounts([100000, 50000])
    assert breakdown.subtotal_vnd == 150000
    assert breakdown.total_vnd == breakdown.subtotal_vnd + breakdown.shipping_fee_vnd
    assert breakdown.shipping_fee_vnd == settings.shipping_flat_fee_vnd


def test_compute_amounts_empty():
    breakdown = compute_amounts([])
    assert breakdown.subtotal_vnd == 0
