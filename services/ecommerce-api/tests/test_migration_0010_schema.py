"""Test that migration 0010 creates the expected multi-city schema."""

from sqlalchemy import CheckConstraint, inspect
from sqlalchemy.dialects.mysql import BIGINT, DATETIME

from app.db.base import Base
from app.models.customer import Customer


def _table_names() -> set[str]:
    return set(Base.metadata.tables.keys())


def _column_names(table_name: str) -> list[str]:
    table = Base.metadata.tables[table_name]
    return [col.name for col in table.columns]


def _check_constraint_names(table_name: str) -> set[str]:
    table = Base.metadata.tables[table_name]
    return {
        constraint.name
        for constraint in table.constraints
        if isinstance(constraint, CheckConstraint) and constraint.name is not None
    }


def test_cities_table_exists() -> None:
    assert "cities" in _table_names()


def test_cities_columns() -> None:
    cols = _column_names("cities")
    assert "city_id" in cols
    assert "code" in cols
    assert "name" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols


def test_cities_primary_key() -> None:
    table = Base.metadata.tables["cities"]
    pk = table.primary_key
    assert len(pk.columns) == 1
    assert pk.columns[0].name == "city_id"


def test_stores_table_exists() -> None:
    assert "stores" in _table_names()


def test_stores_columns() -> None:
    cols = _column_names("stores")
    assert "store_id" in cols
    assert "city_id" in cols
    assert "code" in cols
    assert "name" in cols
    assert "address" in cols
    assert "phone" in cols
    assert "is_active" in cols
    assert "created_at" in cols
    assert "updated_at" in cols


def test_stores_primary_key() -> None:
    table = Base.metadata.tables["stores"]
    pk = table.primary_key
    assert len(pk.columns) == 1
    assert pk.columns[0].name == "store_id"


def test_stores_foreign_key_to_cities() -> None:
    table = Base.metadata.tables["stores"]
    fk_cols = [fk.parent.name for fk in table.foreign_keys]
    assert "city_id" in fk_cols


def test_store_inventory_table_exists() -> None:
    assert "store_inventory" in _table_names()


def test_store_inventory_columns() -> None:
    cols = _column_names("store_inventory")
    assert "store_id" in cols
    assert "variant_id" in cols
    assert "on_hand" in cols
    assert "opening_on_hand" in cols
    assert "version" in cols
    assert "updated_at" in cols


def test_store_inventory_composite_primary_key() -> None:
    table = Base.metadata.tables["store_inventory"]
    pk = table.primary_key
    pk_col_names = [col.name for col in pk.columns]
    assert set(pk_col_names) == {"store_id", "variant_id"}


def test_store_inventory_foreign_keys() -> None:
    table = Base.metadata.tables["store_inventory"]
    fk_target_map = {fk.target_fullname: fk.parent.name for fk in table.foreign_keys}
    assert "stores.store_id" in fk_target_map
    assert "product_variants.variant_id" in fk_target_map


def test_customers_has_city_id_column() -> None:
    assert "city_id" in Customer.__table__.columns


def test_customers_has_store_id_column() -> None:
    assert "store_id" in Customer.__table__.columns


def test_customers_role_constraint_includes_new_roles() -> None:
    names = _check_constraint_names("customers")
    assert "ck_customers_role" in names
    table = Base.metadata.tables["customers"]
    for constraint in table.constraints:
        if isinstance(constraint, CheckConstraint) and constraint.name == "ck_customers_role":
            sql = str(constraint.sqltext)
            assert "store_manager" in sql
            assert "city_planner" in sql
            break
    else:
        raise AssertionError("ck_customers_role check constraint not found")


def test_cities_unique_code() -> None:
    table = Base.metadata.tables["cities"]
    unique_indexes = [
        idx for idx in table.indexes if idx.unique
    ]
    code_in_unique = any(
        len(idx.columns) == 1 and idx.columns[0].name == "code"
        for idx in unique_indexes
    )
    assert code_in_unique, "cities.code should have a unique index"


def test_stores_unique_code() -> None:
    table = Base.metadata.tables["stores"]
    unique_indexes = [
        idx for idx in table.indexes if idx.unique
    ]
    code_in_unique = any(
        len(idx.columns) == 1 and idx.columns[0].name == "code"
        for idx in unique_indexes
    )
    assert code_in_unique, "stores.code should have a unique index"


def test_store_inventory_unique_constraint() -> None:
    table = Base.metadata.tables["store_inventory"]
    unique_indexes = [
        idx for idx in table.indexes if idx.unique
    ]
    has_store_variant = any(
        {col.name for col in idx.columns} == {"store_id", "variant_id"}
        for idx in unique_indexes
    )
    assert has_store_variant, "store_inventory should have a unique (store_id, variant_id) index"


def test_customer_city_id_nullable() -> None:
    col = Customer.__table__.c.city_id
    assert col.nullable is True


def test_customer_store_id_nullable() -> None:
    col = Customer.__table__.c.store_id
    assert col.nullable is True
