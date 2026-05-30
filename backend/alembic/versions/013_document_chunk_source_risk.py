"""Add source risk metadata to document chunks

Revision ID: 013
Revises: 012
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "documentchunk",
        sa.Column("source_risk_level", sa.String(), nullable=False, server_default="low"),
    )
    op.add_column(
        "documentchunk",
        sa.Column("source_risk_flags_json", sa.String(), nullable=False, server_default="[]"),
    )


def downgrade() -> None:
    op.drop_column("documentchunk", "source_risk_flags_json")
    op.drop_column("documentchunk", "source_risk_level")
