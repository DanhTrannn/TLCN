from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("Sup3rSecret!")
    assert hashed != "Sup3rSecret!"
    assert verify_password(hashed, "Sup3rSecret!") is True
    assert verify_password(hashed, "wrong") is False


def test_token_roundtrip_contains_public_id():
    token = create_access_token("public-abc")
    claims = decode_access_token(token)
    assert claims is not None
    assert claims["sub"] == "public-abc"


def test_decode_invalid_token_returns_none():
    assert decode_access_token("not-a-jwt") is None
