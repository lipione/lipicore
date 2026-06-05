"""Add bank feature flags

Revision ID: 014
Revises: 013
Create Date: 2026-06-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "014"
down_revision: Union[str, None] = "013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bankfeatureflag",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("feature_key", sa.String(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("configured_by_user_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["configured_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id", "feature_key", name="uq_bank_feature_flag_bank_feature"),
    )
    op.create_index("ix_bankfeatureflag_bank_id", "bankfeatureflag", ["bank_id"])
    op.create_index("ix_bankfeatureflag_feature_key", "bankfeatureflag", ["feature_key"])


def downgrade() -> None:
    op.drop_index("ix_bankfeatureflag_feature_key", table_name="bankfeatureflag")
    op.drop_index("ix_bankfeatureflag_bank_id", table_name="bankfeatureflag")
    op.drop_table("bankfeatureflag")
