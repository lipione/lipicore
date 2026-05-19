"""Backfill approved document lifecycle state

Revision ID: 005
Revises: 004
Create Date: 2026-05-19 02:40:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE document
        SET version_state = 'approved',
            approved_at = COALESCE(approved_at, created_at)
        WHERE status = 'approved'
          AND version_state = 'draft'
        """
    )
    op.execute(
        """
        UPDATE documentchunk c
        SET
            document_status = d.status,
            version_state = d.version_state,
            department = d.department,
            access_level = d.access_level,
            document_scope = d.document_scope,
            session_id = d.session_id
        FROM document d
        WHERE d.id = c.document_id
        """
    )


def downgrade() -> None:
    pass
