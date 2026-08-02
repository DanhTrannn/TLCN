from types import SimpleNamespace

import pytest

from app.core.errors import ACCOUNT_LOCKED, INVALID_CREDENTIALS, AppError
from app.core.security import hash_password
from app.modules.auth.service import _validate_credentials


def credential(*, enabled: bool = True):
    return SimpleNamespace(
        password_hash=hash_password("CorrectPassword@123"),
        is_enabled=enabled,
    )


def test_locked_account_with_correct_password_returns_locked_error() -> None:
    customer = SimpleNamespace(status="inactive")

    with pytest.raises(AppError) as raised:
        _validate_credentials(customer, credential(), "CorrectPassword@123")

    assert raised.value.code == ACCOUNT_LOCKED
    assert raised.value.status_code == 403
    assert raised.value.message == "Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên."


def test_locked_account_with_wrong_password_keeps_generic_error() -> None:
    customer = SimpleNamespace(status="inactive")

    with pytest.raises(AppError) as raised:
        _validate_credentials(customer, credential(), "WrongPassword@123")

    assert raised.value.code == INVALID_CREDENTIALS
    assert raised.value.status_code == 401


def test_disabled_credential_returns_locked_error() -> None:
    customer = SimpleNamespace(status="active")

    with pytest.raises(AppError) as raised:
        _validate_credentials(customer, credential(enabled=False), "CorrectPassword@123")

    assert raised.value.code == ACCOUNT_LOCKED
