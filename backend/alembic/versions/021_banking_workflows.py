"""banking workflows

Revision ID: 021
Revises: 020
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bankingworkflowcase",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("workflow_type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("prompt", sa.String(), nullable=False),
        sa.Column("output_summary", sa.String(), nullable=False),
        sa.Column("customer_reference", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["assigned_to_user_id", "bank_id", "created_at", "created_by_user_id", "customer_reference", "priority", "status", "workflow_type"]:
        op.create_index(f"ix_bankingworkflowcase_{column}", "bankingworkflowcase", [column])

    op.create_table(
        "auditevidencepack",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("summary", sa.String(), nullable=True),
        sa.Column("included_items_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["bank_id", "created_at", "created_by_user_id", "source_type"]:
        op.create_index(f"ix_auditevidencepack_{column}", "auditevidencepack", [column])


def downgrade() -> None:
    for column in ["source_type", "created_by_user_id", "created_at", "bank_id"]:
        op.drop_index(f"ix_auditevidencepack_{column}", table_name="auditevidencepack")
    op.drop_table("auditevidencepack")
    for column in ["workflow_type", "status", "priority", "customer_reference", "created_by_user_id", "created_at", "bank_id", "assigned_to_user_id"]:
        op.drop_index(f"ix_bankingworkflowcase_{column}", table_name="bankingworkflowcase")
    op.drop_table("bankingworkflowcase")
