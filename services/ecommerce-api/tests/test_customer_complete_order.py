from types import SimpleNamespace

import pytest

from app.core.errors import INVALID_STATE_TRANSITION, RESOURCE_NOT_FOUND, AppError
from app.main import app
from app.modules.orders import service


class Result:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value


class Session:
    def __init__(self, results):
        self._results = iter(results)
        self.added = []
        self.flushed = False

    def execute(self, _statement):
        return Result(next(self._results))

    def add(self, value):
        self.added.append(value)

    def flush(self):
        self.flushed = True


def order(status: str = "confirmed"):
    return SimpleNamespace(
        order_id=10,
        customer_id=99,
        order_number="ORD-20260802-0001",
        status=status,
        updated_at=None,
        completed_at=None,
    )


def run_complete(monkeypatch, session: Session, owner_customer_id: int = 99):
    monkeypatch.setattr(service, "run_in_transaction", lambda work: work(session))
    return service.complete_order(
        "ORD-20260802-0001",
        "complete-request-1",
        transition_source="customer",
        owner_customer_id=owner_customer_id,
    )


def test_owner_completes_confirmed_order(monkeypatch) -> None:
    current_order = order()
    session = Session([current_order, None])

    response = run_complete(monkeypatch, session)

    assert response.status == "completed"
    assert current_order.status == "completed"
    assert current_order.completed_at is not None
    assert session.flushed is True
    history = session.added[0]
    assert history.from_status == "confirmed"
    assert history.to_status == "completed"
    assert history.transition_source == "customer"


def test_customer_cannot_complete_another_customers_order(monkeypatch) -> None:
    session = Session([order()])

    with pytest.raises(AppError) as error:
        run_complete(monkeypatch, session, owner_customer_id=100)

    assert error.value.code == RESOURCE_NOT_FOUND
    assert error.value.status_code == 404
    assert session.added == []


def test_customer_cannot_complete_order_before_admin_confirmation(monkeypatch) -> None:
    session = Session([order(status="paid"), None])

    with pytest.raises(AppError) as error:
        run_complete(monkeypatch, session)

    assert error.value.code == INVALID_STATE_TRANSITION
    assert error.value.status_code == 409
    assert session.added == []


def test_only_customer_complete_route_is_exposed() -> None:
    paths = {route.path for route in app.routes}

    assert "/api/v1/orders/{order_number}/complete" in paths
    assert "/api/v1/admin/orders/{order_number}/complete" not in paths
    assert "/internal/v1/orders/{order_number}/complete" not in paths
