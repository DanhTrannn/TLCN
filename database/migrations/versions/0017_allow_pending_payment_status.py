"""allow pending payment status in check constraints

Revision ID: 0017
Revises: 0016
Create Date: 2026-09-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        inspector = sa.inspect(bind)
        check_names = {c["name"] for c in inspector.get_check_constraints("payments") if c.get("name")}
        for ck in check_names:
            if "status" in ck:
                op.execute(f"ALTER TABLE payments DROP CHECK {ck}")
            elif "failure_code_consistency" in ck:
                op.execute(f"ALTER TABLE payments DROP CHECK {ck}")

        op.execute(
            "ALTER TABLE payments ADD CONSTRAINT ck_payments_status "
            "CHECK (status in ('succeeded','failed','pending'))"
        )
        op.execute(
            "ALTER TABLE payments ADD CONSTRAINT ck_payments_failure_code_consistency "
            "CHECK (((status in ('succeeded','pending') and failure_code is null) or "
            "(status = 'failed' and failure_code is not null)))"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        inspector = sa.inspect(bind)
        check_names = {c["name"] for c in inspector.get_check_constraints("payments") if c.get("name")}
        for ck in check_names:
            if "status" in ck:
                op.execute(f"ALTER TABLE payments DROP CHECK {ck}")
            elif "failure_code_consistency" in ck:
                op.execute(f"ALTER TABLE payments DROP CHECK {ck}")

        op.execute(
            "ALTER TABLE payments ADD CONSTRAINT ck_payments_status "
            "CHECK (status in ('succeeded','failed'))"
        )
        op.execute(
            "ALTER TABLE payments ADD CONSTRAINT ck_payments_failure_code_consistency "
            "CHECK (((status = 'succeeded' and failure_code is null) or "
            "(status = 'failed' and failure_code is not null)))"
        )
