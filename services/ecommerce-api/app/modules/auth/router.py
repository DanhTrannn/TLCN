from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_current_customer, get_db, verify_csrf
from app.models.customer import Customer, CustomerCredential
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


@router.post("/register", response_model=CustomerResponse, status_code=201)
def register(payload: RegisterRequest, response: Response) -> CustomerResponse:
    customer = register_customer(payload.email, payload.password, payload.display_name)
    set_auth_cookies(response, str(customer.public_id))
    return CustomerResponse(
        public_id=str(customer.public_id),
        display_name=customer.display_name,
        email=str(payload.email).strip().lower(),
        role=customer.role,
    )


@router.post("/login", response_model=CustomerResponse)
def login(payload: LoginRequest, response: Response) -> CustomerResponse:
    customer, email_normalized = authenticate(payload.email, payload.password)
    set_auth_cookies(response, str(customer.public_id))
    return CustomerResponse(
        public_id=str(customer.public_id),
        display_name=customer.display_name,
        email=email_normalized,
        role=customer.role,
    )


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
    return CustomerResponse(
        public_id=str(customer.public_id),
        display_name=customer.display_name,
        email=_email_for(db, customer.customer_id),
        role=customer.role,
    )
