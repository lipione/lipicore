"""Add long document analysis jobs

Revision ID: 012
Revises: 011
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "long_document_analysis_job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("requested_by", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=True),
        sa.Column("analysis_type", sa.String(), nullable=False),
        sa.Column("prompt", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("result_text", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["document.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["user.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["chatsession.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_long_document_analysis_job_bank_updated",
        "long_document_analysis_job",
        ["bank_id", "updated_at"],
    )
    op.create_index(
        "ix_long_document_analysis_job_document",
        "long_document_analysis_job",
        ["document_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_long_document_analysis_job_document", table_name="long_document_analysis_job")
    op.drop_index("ix_long_document_analysis_job_bank_updated", table_name="long_document_analysis_job")
    op.drop_table("long_document_analysis_job")
