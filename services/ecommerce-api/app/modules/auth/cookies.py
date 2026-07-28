from fastapi import Response

from app.core.config import get_settings
from app.core.security import create_access_token, generate_csrf_token


def set_auth_cookies(response: Response, public_id: str) -> None:
    settings = get_settings()
    token = create_access_token(public_id)
    csrf = generate_csrf_token()
    max_age = settings.access_token_ttl_minutes * 60
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )
    # CSRF cookie is readable by JS (double-submit pattern), not HttpOnly.
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        domain=settings.cookie_domain,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    for name in (settings.auth_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(
            key=name,
            domain=settings.cookie_domain,
            path="/",
        )
