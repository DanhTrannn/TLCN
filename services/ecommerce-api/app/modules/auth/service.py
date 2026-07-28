from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import (
    EMAIL_ALREADY_EXISTS,
    INVALID_CREDENTIALS,
    AppError,
)
from app.core.ids import uuid7
from app.core.security import hash_password, needs_rehash, verify_password
from app.db.uow import run_in_transaction
from app.models.customer import Customer, CustomerCredential


def normalize_email(email: str) -> str:
    return email.strip().lower()


def register_customer(email: str, password: str, display_name: str) -> Customer:
    email_normalized = normalize_email(email)
    password_hash = hash_password(password)
    public_id = uuid7()

    def _work(db: Session) -> Customer:
        customer = Customer(
            public_id=public_id,
            role="customer",
            display_name=display_name.strip(),
            status="active",
            data_origin="manual",
        )
        db.add(customer)
        db.flush()
        db.add(
            CustomerCredential(
                customer_id=customer.customer_id,
                email_normalized=email_normalized,
                password_hash=password_hash,
                is_enabled=True,
            )
        )
        db.flush()
        db.refresh(customer)
        return customer

    try:
        return run_in_transaction(_work)
    except IntegrityError as error:
        raise AppError(
            EMAIL_ALREADY_EXISTS, "Email đã được đăng ký.", status_code=409
        ) from error


def authenticate(email: str, password: str) -> tuple[Customer, str]:
    """Return (customer, email_normalized) on success, else raise INVALID_CREDENTIALS."""
    email_normalized = normalize_email(email)

    def _work(db: Session) -> tuple[Customer, CustomerCredential]:
        row = db.execute(
            select(Customer, CustomerCredential)
            .join(CustomerCredential, CustomerCredential.customer_id == Customer.customer_id)
            .where(CustomerCredential.email_normalized == email_normalized)
        ).first()
        if row is None:
            raise AppError(INVALID_CREDENTIALS, "Email hoặc mật khẩu không đúng.", status_code=401)
        customer, credential = row
        if not credential.is_enabled or customer.status != "active":
            raise AppError(INVALID_CREDENTIALS, "Email hoặc mật khẩu không đúng.", status_code=401)
        if not verify_password(credential.password_hash, password):
            raise AppError(INVALID_CREDENTIALS, "Email hoặc mật khẩu không đúng.", status_code=401)
        if needs_rehash(credential.password_hash):
            credential.password_hash = hash_password(password)
            credential.password_changed_at = datetime.now(UTC)
        db.expunge(customer)
        return customer, credential

    customer, _ = run_in_transaction(_work)
    return customer, email_normalized
