from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_current_customer, get_db, verify_csrf
from app.models.customer import Customer, CustomerCredential
from app.models.multicity import Store
from app.modules.auth.cookies import clear_auth_cookies, set_auth_cookies
from app.modules.auth.schemas import CustomerResponse, LoginRequest, RegisterRequest
from app.modules.auth.service import authenticate, register_customer

router = APIRouter(prefix="/auth", tags=["auth"])


def _email_for(db: Session, customer_id: int) -> str:
    return db.execute(
        select(CustomerCredential.email_normalized).where(
            CustomerCredential.customer_id == customer_id
        )
    ).scalar_one()


def _store_name_for(db: Session, store_id: int | None) -> str | None:
    if not store_id:
        return None
    store = db.execute(
        select(Store.name).where(Store.store_id == store_id)
    ).scalar_one_or_none()
    return store


def _customer_response(db: Session, customer: Customer, email: str) -> CustomerResponse:
    return CustomerResponse(
        public_id=str(customer.public_id),
        display_name=customer.display_name,
        email=email,
        role=customer.role,
        store_id=customer.store_id,
        store_name=_store_name_for(db, customer.store_id),
    )


@router.post("/register", response_model=CustomerResponse, status_code=201)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> CustomerResponse:
    customer = register_customer(payload.email, payload.password, payload.display_name)
    set_auth_cookies(response, str(customer.public_id))
    return _customer_response(db, customer, str(payload.email).strip().lower())


@router.post("/login", response_model=CustomerResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> CustomerResponse:
    customer, email_normalized = authenticate(payload.email, payload.password)
    set_auth_cookies(response, str(customer.public_id))
    return _customer_response(db, customer, email_normalized)


@router.post("/logout", status_code=204)
def logout(response: Response, _: None = Depends(verify_csrf)) -> Response:
    clear_auth_cookies(response)
    response.status_code = 204
    return response


@router.get("/me", response_model=CustomerResponse)
def me(
    customer: Customer = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> CustomerResponse:
    return _customer_response(db, customer, _email_for(db, customer.customer_id))
