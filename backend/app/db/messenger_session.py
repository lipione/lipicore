from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from ..core.config import settings


messenger_engine = create_engine(settings.MESSENGER_DATABASE_URL, echo=False)


def get_messenger_session():
    with Session(messenger_engine) as session:
        yield session


def init_messenger_db():
    from ..models.bank import Bank  # noqa: F401
    from ..models.chat import ChatMessage, ChatSession  # noqa: F401
    from ..models.document import Document, DocumentChunk  # noqa: F401
    from ..models.messenger import (  # noqa: F401
        MessengerAttachment,
        MessengerAuditEvent,
        MessengerConversation,
        MessengerMembership,
        MessengerMessage,
        MessengerPolicy,
    )
    from ..models.token import RevokedToken  # noqa: F401
    from ..models.user import User  # noqa: F401

    SQLModel.metadata.create_all(messenger_engine)
    ensure_messenger_schema(messenger_engine)


def ensure_messenger_schema(engine=messenger_engine):
    inspector = inspect(engine)
    if "messenger_message" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("messenger_message")}
    dialect = engine.dialect.name
    datetime_type = "TIMESTAMP" if dialect == "postgresql" else "DATETIME"
    column_defs = {
        "reply_to_message_id": "INTEGER",
        "edited_at": datetime_type,
        "pinned_at": datetime_type,
        "pinned_by": "INTEGER",
    }
    missing = [
        (column, column_type)
        for column, column_type in column_defs.items()
        if column not in existing_columns
    ]
    if not missing:
        return

    with engine.begin() as connection:
        for column, column_type in missing:
            connection.execute(text(f"ALTER TABLE messenger_message ADD COLUMN {column} {column_type}"))
