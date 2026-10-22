import pytest
from lakehouse.oltp.silver import (
    _PII_COLUMN_PATTERN,
    _get_salt,
    _pseudonymized_column_name,
)


def test_get_salt_raises_value_error_when_missing(monkeypatch):
    monkeypatch.delenv("SILVER_PSEUDONYMIZE_SALT", raising=False)
    with pytest.raises(ValueError, match="SILVER_PSEUDONYMIZE_SALT is required and must not be empty"):
        _get_salt()

    monkeypatch.setenv("SILVER_PSEUDONYMIZE_SALT", "   ")
    with pytest.raises(ValueError, match="SILVER_PSEUDONYMIZE_SALT is required and must not be empty"):
        _get_salt()


def test_get_salt_returns_configured_value(monkeypatch):
    monkeypatch.setenv("SILVER_PSEUDONYMIZE_SALT", "my_secure_salt_value")
    assert _get_salt() == "my_secure_salt_value"


def test_pseudonymized_column_names_match_silver_contract():
    assert _pseudonymized_column_name("email_normalized") == "email_pseudonymized"
    assert _pseudonymized_column_name("receiver_phone") == "receiver_phone_pseudonymized"


@pytest.mark.parametrize(
    "column_name",
    [
        "email_normalized",
        "phone",
        "full_name",
        "receiver_name",
        "receiver_phone",
        "shipping_address_text",
    ],
)
def test_quarantine_pii_detection(column_name):
    assert _PII_COLUMN_PATTERN.search(column_name)
