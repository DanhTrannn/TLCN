import uuid

from sqlalchemy import BINARY
from sqlalchemy.types import TypeDecorator


class GUID(TypeDecorator):
    """Store UUID as BINARY(16); expose as uuid.UUID / canonical string."""

    impl = BINARY(16)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value.bytes
        return uuid.UUID(str(value)).bytes

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return uuid.UUID(bytes=bytes(value))
