"""notifications

Revision ID: 017
Revises: 016
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("action_url", sa.String(), nullable=True),
        sa.Column("requires_acknowledgement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notification_bank_id", "notification", ["bank_id"])
    op.create_index("ix_notification_category", "notification", ["category"])
    op.create_index("ix_notification_created_at", "notification", ["created_at"])
    op.create_index("ix_notification_recipient_user_id", "notification", ["recipient_user_id"])
    op.create_index("ix_notification_severity", "notification", ["severity"])
    op.create_index("ix_notification_source_type", "notification", ["source_type"])


def downgrade() -> None:
    op.drop_index("ix_notification_source_type", table_name="notification")
    op.drop_index("ix_notification_severity", table_name="notification")
    op.drop_index("ix_notification_recipient_user_id", table_name="notification")
    op.drop_index("ix_notification_created_at", table_name="notification")
    op.drop_index("ix_notification_category", table_name="notification")
    op.drop_index("ix_notification_bank_id", table_name="notification")
    op.drop_table("notification")
