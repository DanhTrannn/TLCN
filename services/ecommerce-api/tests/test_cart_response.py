from app.core.config import get_settings
from app.modules.cart.service import _empty_cart


def test_empty_cart_exposes_free_shipping_threshold() -> None:
    response = _empty_cart()

    assert response.free_shipping_threshold_vnd == get_settings().free_shipping_threshold_vnd
