"""Add document chunk full-text indexes

Revision ID: 003
Revises: 002
Create Date: 2026-05-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_documentchunk_fts_simple
        ON documentchunk
        USING gin (to_tsvector('simple', coalesce(chunk_text, '')))
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_documentchunk_bank_document
        ON documentchunk (bank_id, document_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_documentchunk_bank_document")
    op.execute("DROP INDEX IF EXISTS ix_documentchunk_fts_simple")
