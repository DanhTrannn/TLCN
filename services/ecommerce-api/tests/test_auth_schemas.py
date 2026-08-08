from app.modules.auth.schemas import LoginRequest


def test_login_accepts_bootstrap_admin_local_email() -> None:
    payload = LoginRequest(email=" admin@web.local ", password="Admin@12345")

    assert payload.email == "admin@web.local"
