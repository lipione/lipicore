"""add policy citation metadata to document chunks

Revision ID: 022
Revises: 021
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa


revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documentchunk", sa.Column("printed_page_number", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("document_heading", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("clause_number", sa.String(), nullable=True))
    op.add_column("documentchunk", sa.Column("citation_confidence", sa.Float(), nullable=True))
    op.add_column(
        "documentchunk",
        sa.Column("citation_incomplete_reasons_json", sa.String(), nullable=False, server_default="[]"),
    )


def downgrade():
    op.drop_column("documentchunk", "citation_incomplete_reasons_json")
    op.drop_column("documentchunk", "citation_confidence")
    op.drop_column("documentchunk", "clause_number")
    op.drop_column("documentchunk", "document_heading")
    op.drop_column("documentchunk", "printed_page_number")
