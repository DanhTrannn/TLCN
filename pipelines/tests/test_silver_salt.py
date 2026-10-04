import pytest
from lakehouse.oltp.silver import _get_salt


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
