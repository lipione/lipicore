"""Secure messenger addon

Revision ID: 006
Revises: 005
Create Date: 2026-05-19 04:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if inspector.has_table("messenger_policy"):
        return

    op.create_table(
        "messenger_policy",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_staff_groups", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_cross_department_groups", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("allow_web_downloads", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("max_group_members", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("max_file_size_mb", sa.Integer(), nullable=False, server_default="25"),
        sa.Column("allowed_file_types_json", sa.String(), nullable=False, server_default='["pdf","docx","xlsx","xls","png","jpg","jpeg","txt"]'),
        sa.Column("retention_days", sa.Integer(), nullable=False, server_default="365"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id", name="uq_messenger_policy_bank_id"),
    )
    op.create_index("ix_messenger_policy_bank_id", "messenger_policy", ["bank_id"])

    op.create_table(
        "messenger_conversation",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("department", sa.String(), nullable=True),
        sa.Column("direct_key", sa.String(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_id", "type", "direct_key", name="uq_messenger_direct_key"),
        sa.UniqueConstraint("bank_id", "type", "department", name="uq_messenger_department"),
    )
    op.create_index("ix_messenger_conversation_bank_id", "messenger_conversation", ["bank_id"])
    op.create_index("ix_messenger_conversation_type", "messenger_conversation", ["type"])
    op.create_index("ix_messenger_conversation_department", "messenger_conversation", ["department"])
    op.create_index("ix_messenger_conversation_direct_key", "messenger_conversation", ["direct_key"])
    op.create_index("ix_messenger_conversation_is_active", "messenger_conversation", ["is_active"])

    op.create_table(
        "messenger_membership",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="member"),
        sa.Column("source", sa.String(), nullable=False, server_default="manual"),
        sa.Column("last_read_message_id", sa.Integer(), nullable=True),
        sa.Column("last_read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["messenger_conversation.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_messenger_membership_user"),
    )
    op.create_index("ix_messenger_membership_bank_id", "messenger_membership", ["bank_id"])
    op.create_index("ix_messenger_membership_conversation_id", "messenger_membership", ["conversation_id"])
    op.create_index("ix_messenger_membership_user_id", "messenger_membership", ["user_id"])
    op.create_index("ix_messenger_membership_last_read_message_id", "messenger_membership", ["last_read_message_id"])

    op.create_table(
        "messenger_message",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("sender_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="sent"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["messenger_conversation.id"]),
        sa.ForeignKeyConstraint(["sender_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messenger_message_bank_id", "messenger_message", ["bank_id"])
    op.create_index("ix_messenger_message_conversation_id", "messenger_message", ["conversation_id"])
    op.create_index("ix_messenger_message_sender_id", "messenger_message", ["sender_id"])
    op.create_index("ix_messenger_message_created_at", "messenger_message", ["created_at"])

    op.create_table(
        "messenger_attachment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("stored_filename", sa.String(), nullable=False),
        sa.Column("stored_path", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["conversation_id"], ["messenger_conversation.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messenger_message.id"]),
        sa.ForeignKeyConstraint(["uploaded_by"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messenger_attachment_bank_id", "messenger_attachment", ["bank_id"])
    op.create_index("ix_messenger_attachment_conversation_id", "messenger_attachment", ["conversation_id"])
    op.create_index("ix_messenger_attachment_message_id", "messenger_attachment", ["message_id"])
    op.create_index("ix_messenger_attachment_uploaded_by", "messenger_attachment", ["uploaded_by"])

    op.create_table(
        "messenger_audit_event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("bank_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("resource_type", sa.String(), nullable=False),
        sa.Column("resource_id", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["bank_id"], ["bank.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_messenger_audit_event_bank_id", "messenger_audit_event", ["bank_id"])
    op.create_index("ix_messenger_audit_event_user_id", "messenger_audit_event", ["user_id"])
    op.create_index("ix_messenger_audit_event_action", "messenger_audit_event", ["action"])
    op.create_index("ix_messenger_audit_event_created_at", "messenger_audit_event", ["created_at"])


def downgrade() -> None:
    op.drop_table("messenger_audit_event")
    op.drop_table("messenger_attachment")
    op.drop_table("messenger_message")
    op.drop_table("messenger_membership")
    op.drop_table("messenger_conversation")
    op.drop_table("messenger_policy")
