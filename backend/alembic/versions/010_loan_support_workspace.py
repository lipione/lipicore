"""Add loan support workspace

Revision ID: 010
Revises: 009
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loan_support_case",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("assigned_to", sa.Integer(), nullable=True),
        sa.Column("applicant_name", sa.String(), nullable=False),
        sa.Column("loan_type", sa.String(), nullable=False),
        sa.Column("requested_amount", sa.Float(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("required_documents_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("received_documents_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("missing_documents_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("risk_factors_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("source_document_ids_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("credit_memo_draft", sa.String(), nullable=True),
        sa.Column("human_review_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("automated_decision", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["user.id"]),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("loan_support_case")
