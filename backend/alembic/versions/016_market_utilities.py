"""market utilities

Revision ID: 016
Revises: 015
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exchangeratebatch",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exchangeratebatch_bank_id", "exchangeratebatch", ["bank_id"])
    op.create_index("ix_exchangeratebatch_published_at", "exchangeratebatch", ["published_at"])

    op.create_table(
        "exchangerate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("currency_code", sa.String(), nullable=False),
        sa.Column("currency_name", sa.String(), nullable=False),
        sa.Column("unit", sa.Integer(), nullable=False),
        sa.Column("buy_rate", sa.Float(), nullable=False),
        sa.Column("sell_rate", sa.Float(), nullable=False),
        sa.Column("middle_rate", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["batch_id"], ["exchangeratebatch.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_exchangerate_bank_id", "exchangerate", ["bank_id"])
    op.create_index("ix_exchangerate_batch_id", "exchangerate", ["batch_id"])
    op.create_index("ix_exchangerate_currency_code", "exchangerate", ["currency_code"])

    op.create_table(
        "bankingcalendarevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("branch", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_bankingcalendarevent_bank_id", "bankingcalendarevent", ["bank_id"])
    op.create_index("ix_bankingcalendarevent_branch", "bankingcalendarevent", ["branch"])
    op.create_index("ix_bankingcalendarevent_event_type", "bankingcalendarevent", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_bankingcalendarevent_event_type", table_name="bankingcalendarevent")
    op.drop_index("ix_bankingcalendarevent_branch", table_name="bankingcalendarevent")
    op.drop_index("ix_bankingcalendarevent_bank_id", table_name="bankingcalendarevent")
    op.drop_table("bankingcalendarevent")
    op.drop_index("ix_exchangerate_currency_code", table_name="exchangerate")
    op.drop_index("ix_exchangerate_batch_id", table_name="exchangerate")
    op.drop_index("ix_exchangerate_bank_id", table_name="exchangerate")
    op.drop_table("exchangerate")
    op.drop_index("ix_exchangeratebatch_published_at", table_name="exchangeratebatch")
    op.drop_index("ix_exchangeratebatch_bank_id", table_name="exchangeratebatch")
    op.drop_table("exchangeratebatch")
