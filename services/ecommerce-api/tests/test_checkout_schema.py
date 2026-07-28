import pytest
from pydantic import ValidationError

from app.modules.checkout.schemas import CheckoutRequest


VALID_CHECKOUT = {
    "receiver_name": "Nguyen Van A",
    "receiver_phone": "0900000000",
    "shipping_address_text": "1 Nguyen Hue, Quan 1, TP.HCM",
}


def test_checkout_request_accepts_shipping_information():
    request = CheckoutRequest.model_validate(VALID_CHECKOUT)

    assert request.receiver_name == "Nguyen Van A"
    assert not hasattr(request, "payment_scenario")


def test_checkout_request_rejects_legacy_payment_scenario():
    with pytest.raises(ValidationError):
        CheckoutRequest.model_validate({**VALID_CHECKOUT, "payment_scenario": "force_failure"})
