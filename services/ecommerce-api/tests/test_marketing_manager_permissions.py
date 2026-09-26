"""Integration tests verifying marketing_manager role permissions on coupons & reviews."""

from datetime import UTC, datetime, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.elements import TextClause

from app.core.ids import uuid7
from app.db.base import Base
from app.db.deps import get_current_customer, get_db, verify_csrf
import app.db.deps
import app.db.uow
from app.main import app as fastapi_app
import app.models  # noqa: F401
from app.models.customer import Customer


@compiles(TextClause, "sqlite")
def _compile_text(element, compiler, **kw):
    val = element.text
    if "CURRENT_TIMESTAMP(6)" in val:
        return val.replace("CURRENT_TIMESTAMP(6)", "CURRENT_TIMESTAMP")
    return val


@compiles(BIGINT, "sqlite")
def _compile_bigint(element, compiler, **kw):
    return "INTEGER"


@pytest.fixture()
def setup_marketing_db(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("char_length", 1, lambda s: len(s) if s is not None else 0)

    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    monkeypatch.setattr(app.db.uow, "SessionLocal", testing_session)
    monkeypatch.setattr(app.db.deps, "SessionLocal", testing_session)

    def _get_test_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    fastapi_app.dependency_overrides[verify_csrf] = lambda: None

    db = testing_session()

    admin = Customer(
        customer_id=1,
        public_id=uuid7(),
        role="admin",
        display_name="CEO Admin",
        status="active",
    )
    marketing = Customer(
        customer_id=2,
        public_id=uuid7(),
        role="marketing_manager",
        display_name="Marketing Lead",
        status="active",
    )
    store_mgr = Customer(
        customer_id=3,
        public_id=uuid7(),
        role="store_manager",
        display_name="Store Lead",
        status="active",
    )
    normal_user = Customer(
        customer_id=4,
        public_id=uuid7(),
        role="customer",
        display_name="Normal Customer",
        status="active",
    )
    db.add_all([admin, marketing, store_mgr, normal_user])
    db.commit()

    yield {
        "admin": admin,
        "marketing": marketing,
        "store_mgr": store_mgr,
        "normal_user": normal_user,
    }

    fastapi_app.dependency_overrides.clear()


def test_marketing_manager_can_create_and_list_coupons(setup_marketing_db):
    actors = setup_marketing_db
    marketing_user = actors["marketing"]

    fastapi_app.dependency_overrides[get_current_customer] = lambda: marketing_user
    client = TestClient(fastapi_app)

    now = datetime.now(UTC)
    payload = {
        "code": "MKTG2026",
        "discount_type": "percentage",
        "discount_value": 20,
        "minimum_subtotal_vnd": 100000,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=30)).isoformat(),
        "total_usage_limit": 50,
        "per_customer_usage_limit": 1,
    }

    res = client.post("/api/v1/admin/coupons", json=payload)
    assert res.status_code == 201
    created_coupon = res.json()
    assert created_coupon["code"] == "MKTG2026"
    assert created_coupon["discount_value"] == 20

    res_list = client.get("/api/v1/admin/coupons")
    assert res_list.status_code == 200
    coupons = res_list.json()
    assert len(coupons) == 1
    assert coupons[0]["code"] == "MKTG2026"


def test_admin_can_also_create_and_list_coupons(setup_marketing_db):
    actors = setup_marketing_db
    admin_user = actors["admin"]

    fastapi_app.dependency_overrides[get_current_customer] = lambda: admin_user
    client = TestClient(fastapi_app)

    now = datetime.now(UTC)
    payload = {
        "code": "ADMIN10",
        "discount_type": "percentage",
        "discount_value": 10,
        "minimum_subtotal_vnd": 50000,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=10)).isoformat(),
        "total_usage_limit": 100,
        "per_customer_usage_limit": 2,
    }

    res = client.post("/api/v1/admin/coupons", json=payload)
    assert res.status_code == 201


def test_unauthorized_roles_cannot_manage_coupons(setup_marketing_db):
    actors = setup_marketing_db

    now = datetime.now(UTC)
    payload = {
        "code": "FAILCODE",
        "discount_type": "percentage",
        "discount_value": 15,
        "minimum_subtotal_vnd": 50000,
        "starts_at": now.isoformat(),
        "ends_at": (now + timedelta(days=10)).isoformat(),
        "total_usage_limit": 10,
        "per_customer_usage_limit": 1,
    }

    for unauthorized_actor in [actors["store_mgr"], actors["normal_user"]]:
        fastapi_app.dependency_overrides[get_current_customer] = lambda actor=unauthorized_actor: actor
        client = TestClient(fastapi_app)

        res_post = client.post("/api/v1/admin/coupons", json=payload)
        assert res_post.status_code == 403

        res_get = client.get("/api/v1/admin/coupons")
        assert res_get.status_code == 403


def test_marketing_manager_can_list_reviews(setup_marketing_db):
    actors = setup_marketing_db
    marketing_user = actors["marketing"]

    fastapi_app.dependency_overrides[get_current_customer] = lambda: marketing_user
    client = TestClient(fastapi_app)

    res = client.get("/api/v1/admin/reviews")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_unauthorized_roles_cannot_list_reviews(setup_marketing_db):
    actors = setup_marketing_db

    for unauthorized_actor in [actors["store_mgr"], actors["normal_user"]]:
        fastapi_app.dependency_overrides[get_current_customer] = lambda actor=unauthorized_actor: actor
        client = TestClient(fastapi_app)

        res = client.get("/api/v1/admin/reviews")
        assert res.status_code == 403
