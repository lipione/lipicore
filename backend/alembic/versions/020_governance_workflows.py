"""governance workflows

Revision ID: 020
Revises: 019
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledgegap",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_to_user_id", sa.Integer(), nullable=True),
        sa.Column("resolution_notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["assigned_to_user_id", "bank_id", "created_at", "priority", "source_type", "status", "submitted_by_user_id"]:
        op.create_index(f"ix_knowledgegap_{column}", "knowledgegap", [column])

    op.create_table(
        "policychange",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("impact_summary", sa.String(), nullable=True),
        sa.Column("affected_departments_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("action_items_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("source_document_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("published_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["published_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["document.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ["bank_id", "published_at", "published_by_user_id", "status"]:
        op.create_index(f"ix_policychange_{column}", "policychange", [column])

    op.create_table(
        "policychangeacknowledgement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("policy_change_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["policy_change_id"], ["policychange.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_change_id", "user_id", name="uq_policy_change_ack_user"),
    )
    for column in ["bank_id", "policy_change_id", "user_id"]:
        op.create_index(f"ix_policychangeacknowledgement_{column}", "policychangeacknowledgement", [column])


def downgrade() -> None:
    for column in ["user_id", "policy_change_id", "bank_id"]:
        op.drop_index(f"ix_policychangeacknowledgement_{column}", table_name="policychangeacknowledgement")
    op.drop_table("policychangeacknowledgement")
    for column in ["status", "published_by_user_id", "published_at", "bank_id"]:
        op.drop_index(f"ix_policychange_{column}", table_name="policychange")
    op.drop_table("policychange")
    for column in ["submitted_by_user_id", "status", "source_type", "priority", "created_at", "bank_id", "assigned_to_user_id"]:
        op.drop_index(f"ix_knowledgegap_{column}", table_name="knowledgegap")
    op.drop_table("knowledgegap")
