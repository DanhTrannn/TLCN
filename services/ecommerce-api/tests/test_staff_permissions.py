import pytest

from app.core.errors import AppError
from app.modules.admin.branch_inventory_service import check_store_inventory_permission
from app.models.customer import Customer


def test_admin_has_full_access():
    admin = Customer(role="admin", store_id=None, city_id=None)
    check_store_inventory_permission(admin, target_store_id=2, target_city_id=1)


def test_store_manager_can_edit_own_store():
    manager = Customer(role="store_manager", store_id=1, city_id=1)
    check_store_inventory_permission(manager, target_store_id=1, target_city_id=1)


def test_store_manager_cannot_edit_other_store():
    manager = Customer(role="store_manager", store_id=1, city_id=1)
    with pytest.raises(AppError) as excinfo:
        check_store_inventory_permission(manager, target_store_id=2, target_city_id=1)
    assert excinfo.value.status_code == 403


def test_regular_customer_has_no_permission():
    customer = Customer(role="customer", store_id=None, city_id=None)
    with pytest.raises(AppError) as excinfo:
        check_store_inventory_permission(customer, target_store_id=1, target_city_id=1)
    assert excinfo.value.status_code == 403


# --- get_current_staff dependency ---


def test_get_current_staff_accepts_admin():
    from app.db.deps import get_current_staff

    admin = Customer(role="admin", store_id=None, city_id=None)
    result = get_current_staff(admin)
    assert result.role == "admin"


def test_get_current_staff_accepts_store_manager():
    from app.db.deps import get_current_staff

    manager = Customer(role="store_manager", store_id=1, city_id=1)
    result = get_current_staff(manager)
    assert result.role == "store_manager"


def test_get_current_staff_rejects_customer():
    from app.db.deps import get_current_staff

    customer = Customer(role="customer", store_id=None, city_id=None)
    with pytest.raises(AppError) as excinfo:
        get_current_staff(customer)
    assert excinfo.value.status_code == 403


# --- get_current_marketing_staff dependency ---


def test_get_current_marketing_staff_accepts_admin():
    from app.db.deps import get_current_marketing_staff

    admin = Customer(role="admin", store_id=None, city_id=None)
    result = get_current_marketing_staff(admin)
    assert result.role == "admin"


def test_get_current_marketing_staff_accepts_marketing_manager():
    from app.db.deps import get_current_marketing_staff

    marketing_mgr = Customer(role="marketing_manager", store_id=None, city_id=None)
    result = get_current_marketing_staff(marketing_mgr)
    assert result.role == "marketing_manager"


def test_get_current_marketing_staff_rejects_other_roles():
    from app.db.deps import get_current_marketing_staff

    for non_marketing_role in ["customer", "store_manager", "inventory_manager", "operations_manager", "system_admin"]:
        user = Customer(role=non_marketing_role, store_id=None, city_id=None)
        with pytest.raises(AppError) as excinfo:
            get_current_marketing_staff(user)
        assert excinfo.value.status_code == 403


# --- get_current_inventory_staff dependency ---


def test_get_current_inventory_staff_accepts_admin():
    from app.db.deps import get_current_inventory_staff

    admin = Customer(role="admin", store_id=None, city_id=None)
    result = get_current_inventory_staff(admin)
    assert result.role == "admin"


def test_get_current_inventory_staff_accepts_inventory_manager():
    from app.db.deps import get_current_inventory_staff

    inv_mgr = Customer(role="inventory_manager", store_id=None, city_id=None)
    result = get_current_inventory_staff(inv_mgr)
    assert result.role == "inventory_manager"


def test_get_current_inventory_staff_rejects_other_roles():
    from app.db.deps import get_current_inventory_staff

    for non_inventory_role in ["customer", "store_manager", "marketing_manager", "sales_manager", "operations_manager", "system_admin"]:
        user = Customer(role=non_inventory_role, store_id=None, city_id=None)
        with pytest.raises(AppError) as excinfo:
            get_current_inventory_staff(user)
        assert excinfo.value.status_code == 403


