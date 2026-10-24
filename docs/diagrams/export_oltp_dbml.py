"""Export the current SQLAlchemy OLTP model as a reviewable DBML diagram.

The DBML is a visualization artifact, not a migration or SQL source of truth.
Run from the repository root with: .venv/bin/python docs/diagrams/export_oltp_dbml.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import UniqueConstraint
from sqlalchemy.dialects import mysql


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services" / "ecommerce-api"))

import app.models  # noqa: E402,F401  (populate metadata)
from app.db.base import Base  # noqa: E402


GROUPS = {
    "identity": ("customers", "customer_credentials"),
    "catalog": ("categories", "products", "product_variants", "wishlist_items", "product_reviews"),
    "cart_and_promotions": ("carts", "cart_items", "coupons", "coupon_redemptions"),
    "orders_and_payments": ("orders", "order_items", "payments", "refunds", "order_status_history"),
    "stock_and_receipts": (
        "inventory",
        "store_inventory",
        "inventory_transactions",
        "inbound_receipts",
        "inbound_receipt_items",
    ),
    "locations_and_fulfilment": (
        "cities",
        "stores",
        "delivery_staff",
        "shipments",
        "shipment_attempts",
        "return_requests",
        "return_items",
    ),
}


def dbml_type(column) -> tuple[str, bool]:
    compiled = column.type.compile(dialect=mysql.dialect()).lower()
    unsigned = compiled.endswith(" unsigned")
    if unsigned:
        compiled = compiled.removesuffix(" unsigned")
    if compiled == "bool":
        compiled = "boolean"
    return compiled, unsigned


def one_column_unique(table, column_name: str) -> bool:
    if len(table.primary_key.columns) == 1 and column_name in table.primary_key.columns:
        return True
    for index in table.indexes:
        if index.unique and [column.name for column in index.columns] == [column_name]:
            return True
    for constraint in table.constraints:
        if isinstance(constraint, UniqueConstraint) and [column.name for column in constraint.columns] == [column_name]:
            return True
    return False


def table_block(table) -> list[str]:
    header_color = "#a94728" if table.name == "orders" else "#315b4f"
    lines = [f"Table {table.name} [headercolor: {header_color}] {{"]
    single_pk = len(table.primary_key.columns) == 1
    for column in table.columns:
        type_name, unsigned = dbml_type(column)
        settings: list[str] = []
        if single_pk and column.primary_key:
            settings.append("pk")
        if not column.nullable:
            settings.append("not null")
        notes: list[str] = []
        if unsigned:
            notes.append("unsigned")
        if column.computed is not None:
            notes.append("generated column")
        if notes:
            settings.append(f"note: '{'; '.join(notes)}'")
        suffix = f" [{', '.join(settings)}]" if settings else ""
        lines.append(f"  {column.name} {type_name}{suffix}")

    index_rows: list[str] = []
    if not single_pk:
        key = ", ".join(column.name for column in table.primary_key.columns)
        index_rows.append(f"    ({key}) [pk]")
    for index in sorted(table.indexes, key=lambda value: value.name or ""):
        columns = [column.name for column in index.columns]
        expression = columns[0] if len(columns) == 1 else f"({', '.join(columns)})"
        attributes = [f"name: '{index.name}'"]
        if index.unique:
            attributes.append("unique")
        index_rows.append(f"    {expression} [{', '.join(attributes)}]")
    for constraint in sorted(
        (item for item in table.constraints if isinstance(item, UniqueConstraint)),
        key=lambda value: value.name or "",
    ):
        columns = [column.name for column in constraint.columns]
        expression = columns[0] if len(columns) == 1 else f"({', '.join(columns)})"
        attributes = ["unique"]
        if constraint.name:
            attributes.insert(0, f"name: '{constraint.name}'")
        index_rows.append(f"    {expression} [{', '.join(attributes)}]")
    if index_rows:
        lines.extend(["", "  indexes {", *index_rows, "  }"])
    lines.append("}")
    return lines


def render() -> str:
    tables = Base.metadata.tables
    grouped = {name for members in GROUPS.values() for name in members}
    if len(tables) != 28 or grouped != set(tables):
        raise RuntimeError(f"Expected the documented 28 OLTP tables; model={len(tables)}, grouping={len(grouped)}")

    lines = [
        "// D&K E-Commerce OLTP — 28 tables, generated from app.models SQLAlchemy metadata.",
        "// Regenerate: .venv/bin/python docs/diagrams/export_oltp_dbml.py",
        "// Source of truth: database/migrations/versions/ and services/ecommerce-api/app/models/.",
        "// Visualization only: defaults, CHECK expressions, and server-side behavior remain in migrations.",
        "// customer_credentials contains authentication data and is excluded from Lakehouse extraction.",
        "",
    ]
    for group_name, members in GROUPS.items():
        lines.append(f"// {group_name.replace('_', ' ').title()}")
        for name in members:
            lines.extend(table_block(tables[name]))
            lines.append("")

    lines.append("// Foreign keys. A question mark on the referenced end means the FK is nullable.")
    for table in sorted(tables.values(), key=lambda value: value.name):
        for foreign_key in sorted(table.foreign_keys, key=lambda value: value.parent.name):
            column = foreign_key.parent
            unique = one_column_unique(table, column.name)
            operator = "-" if unique else ">"
            if column.nullable:
                operator += "?"
            target = foreign_key.column
            actions: list[str] = []
            if foreign_key.ondelete:
                actions.append(f"delete: {foreign_key.ondelete.lower()}")
            actions.append("color: #315b4f")
            lines.append(
                f"Ref: {table.name}.{column.name} {operator} "
                f"{target.table.name}.{target.name} [{', '.join(actions)}]"
            )

    lines.append("")
    for group_name, members in GROUPS.items():
        lines.append(f"TableGroup {group_name} [color: #ece6da] {{")
        lines.extend(f"  {name}" for name in members)
        lines.extend(["}", ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the committed DBML differs from the current model")
    args = parser.parse_args()
    target = Path(__file__).with_name("erd-oltp-28-tables.dbml")
    content = render()
    if args.check:
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            raise SystemExit(f"Out of date: {target}")
        print(f"OK {target.relative_to(ROOT)}")
        return
    target.write_text(content, encoding="utf-8")
    print(f"Wrote {target.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
