"""Add document freshness and extraction confidence metadata

Revision ID: 007
Revises: 006
Create Date: 2026-05-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("document", sa.Column("approved_by", sa.Integer(), nullable=True))
    op.add_column("document", sa.Column("effective_from", sa.DateTime(), nullable=True))
    op.add_column("document", sa.Column("effective_to", sa.DateTime(), nullable=True))
    op.add_column("document", sa.Column("review_due_at", sa.DateTime(), nullable=True))
    op.add_column("document", sa.Column("regulator", sa.String(), nullable=True))
    op.add_column("document", sa.Column("jurisdiction", sa.String(), nullable=True))
    op.add_column("document", sa.Column("superseded_reason", sa.String(), nullable=True))
    op.create_foreign_key(
        "fk_document_approved_by_user",
        "document",
        "user",
        ["approved_by"],
        ["id"],
    )

    op.add_column("documentchunk", sa.Column("extraction_confidence", sa.Float(), nullable=True))
    op.add_column("documentchunk", sa.Column("ocr_confidence", sa.Float(), nullable=True))
    op.add_column("documentchunk", sa.Column("table_confidence", sa.Float(), nullable=True))
    op.add_column("documentchunk", sa.Column("page_bbox_json", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("documentchunk", "page_bbox_json")
    op.drop_column("documentchunk", "table_confidence")
    op.drop_column("documentchunk", "ocr_confidence")
    op.drop_column("documentchunk", "extraction_confidence")
    op.drop_constraint("fk_document_approved_by_user", "document", type_="foreignkey")
    op.drop_column("document", "superseded_reason")
    op.drop_column("document", "jurisdiction")
    op.drop_column("document", "regulator")
    op.drop_column("document", "review_due_at")
    op.drop_column("document", "effective_to")
    op.drop_column("document", "effective_from")
    op.drop_column("document", "approved_by")
