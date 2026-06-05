"""ceo messages

Revision ID: 018
Revises: 017
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ceomessage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("body", sa.String(), nullable=False),
        sa.Column("audience_type", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=True),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("requires_acknowledgement", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notify", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("published_by_user_id", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["published_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ceomessage_audience_type", "ceomessage", ["audience_type"])
    op.create_index("ix_ceomessage_bank_id", "ceomessage", ["bank_id"])
    op.create_index("ix_ceomessage_department", "ceomessage", ["department"])
    op.create_index("ix_ceomessage_expires_at", "ceomessage", ["expires_at"])
    op.create_index("ix_ceomessage_priority", "ceomessage", ["priority"])
    op.create_index("ix_ceomessage_published_at", "ceomessage", ["published_at"])
    op.create_index("ix_ceomessage_role", "ceomessage", ["role"])

    op.create_table(
        "ceomessageacknowledgement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["ceomessage.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_ceo_message_ack_user"),
    )
    op.create_index("ix_ceomessageacknowledgement_bank_id", "ceomessageacknowledgement", ["bank_id"])
    op.create_index("ix_ceomessageacknowledgement_message_id", "ceomessageacknowledgement", ["message_id"])
    op.create_index("ix_ceomessageacknowledgement_user_id", "ceomessageacknowledgement", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ceomessageacknowledgement_user_id", table_name="ceomessageacknowledgement")
    op.drop_index("ix_ceomessageacknowledgement_message_id", table_name="ceomessageacknowledgement")
    op.drop_index("ix_ceomessageacknowledgement_bank_id", table_name="ceomessageacknowledgement")
    op.drop_table("ceomessageacknowledgement")
    op.drop_index("ix_ceomessage_role", table_name="ceomessage")
    op.drop_index("ix_ceomessage_published_at", table_name="ceomessage")
    op.drop_index("ix_ceomessage_priority", table_name="ceomessage")
    op.drop_index("ix_ceomessage_expires_at", table_name="ceomessage")
    op.drop_index("ix_ceomessage_department", table_name="ceomessage")
    op.drop_index("ix_ceomessage_bank_id", table_name="ceomessage")
    op.drop_index("ix_ceomessage_audience_type", table_name="ceomessage")
    op.drop_table("ceomessage")
