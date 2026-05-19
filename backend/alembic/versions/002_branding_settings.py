"""Add branding settings

Revision ID: 002
Revises: 001
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "brandingsettings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False, server_default="BankAi"),
        sa.Column("bank_name", sa.String(), nullable=False, server_default="Your Bank"),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("primary_color", sa.String(), nullable=False, server_default="#17324d"),
        sa.Column("accent_color", sa.String(), nullable=False, server_default="#c7902c"),
        sa.Column(
            "welcome_message",
            sa.String(),
            nullable=False,
            server_default="Ask approved bank knowledge, analyze internal files, and draft staff-ready answers.",
        ),
        sa.Column("support_contact", sa.String(), nullable=True),
        sa.Column(
            "disclaimer",
            sa.String(),
            nullable=False,
            server_default="Internal staff use only. Verify critical outputs against approved source documents.",
        ),
        sa.Column(
            "allowed_modes_json",
            sa.String(),
            nullable=False,
            server_default='["ask_knowledge","analyze_file","summarize","draft","translate","compare"]',
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id"),
    )
    op.create_index("ix_brandingsettings_bank_id", "brandingsettings", ["bank_id"])


def downgrade() -> None:
    op.drop_index("ix_brandingsettings_bank_id", table_name="brandingsettings")
    op.drop_table("brandingsettings")
