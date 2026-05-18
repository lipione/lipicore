"""Add document lifecycle and chunk permission metadata

Revision ID: 004
Revises: 003
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("document", sa.Column("version_state", sa.String(), nullable=False, server_default="draft"))
    op.add_column("document", sa.Column("supersedes_document_id", sa.Integer(), nullable=True))
    op.add_column("document", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_document_supersedes_document_id_document",
        "document",
        "document",
        ["supersedes_document_id"],
        ["id"],
    )

    op.add_column("documentchunk", sa.Column("department", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("access_level", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("documentchunk", sa.Column("document_scope", sa.String(), nullable=True, server_default="global_knowledge"))
    op.add_column("documentchunk", sa.Column("session_id", sa.Integer(), nullable=True))
    op.add_column("documentchunk", sa.Column("document_status", sa.String(), nullable=False, server_default="uploaded"))
    op.add_column("documentchunk", sa.Column("version_state", sa.String(), nullable=False, server_default="draft"))
    op.execute(
        """
        UPDATE documentchunk c
        SET
            department = d.department,
            access_level = d.access_level,
            document_scope = d.document_scope,
            session_id = d.session_id,
            document_status = d.status,
            version_state = d.version_state
        FROM document d
        WHERE d.id = c.document_id
        """
    )
    op.create_index(
        "ix_documentchunk_permission_scope",
        "documentchunk",
        ["bank_id", "document_scope", "document_status", "version_state", "access_level"],
    )


def downgrade() -> None:
    op.drop_index("ix_documentchunk_permission_scope", table_name="documentchunk")
    op.drop_column("documentchunk", "version_state")
    op.drop_column("documentchunk", "document_status")
    op.drop_column("documentchunk", "session_id")
    op.drop_column("documentchunk", "document_scope")
    op.drop_column("documentchunk", "access_level")
    op.drop_column("documentchunk", "department")
    op.drop_constraint("fk_document_supersedes_document_id_document", "document", type_="foreignkey")
    op.drop_column("document", "approved_at")
    op.drop_column("document", "supersedes_document_id")
    op.drop_column("document", "version_state")
