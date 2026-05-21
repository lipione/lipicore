"""Add support case workspace

Revision ID: 008
Revises: 007
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "support_case",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("customer_issue", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("draft_response", sa.String(), nullable=True),
        sa.Column("escalation_target", sa.String(), nullable=True),
        sa.Column("staff_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("source_document_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("answer_metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["user.id"]),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("support_case")
