"""employee profiles

Revision ID: 015
Revises: 014
Create Date: 2026-06-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "employeeprofile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("branch", sa.String(), nullable=True),
        sa.Column("job_title", sa.String(), nullable=True),
        sa.Column("phone_extension", sa.String(), nullable=True),
        sa.Column("supervisor_user_id", sa.Integer(), nullable=True),
        sa.Column("expertise_tags_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("escalation_areas_json", sa.String(), nullable=False, server_default="[]"),
        sa.Column("availability_status", sa.String(), nullable=False, server_default="available"),
        sa.Column("public_notes", sa.String(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["supervisor_user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_employeeprofile_user_id"),
    )
    op.create_index("ix_employeeprofile_bank_id", "employeeprofile", ["bank_id"])
    op.create_index("ix_employeeprofile_branch", "employeeprofile", ["branch"])
    op.create_index("ix_employeeprofile_job_title", "employeeprofile", ["job_title"])
    op.create_index("ix_employeeprofile_user_id", "employeeprofile", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_employeeprofile_user_id", table_name="employeeprofile")
    op.drop_index("ix_employeeprofile_job_title", table_name="employeeprofile")
    op.drop_index("ix_employeeprofile_branch", table_name="employeeprofile")
    op.drop_index("ix_employeeprofile_bank_id", table_name="employeeprofile")
    op.drop_table("employeeprofile")
