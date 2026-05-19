from sqlmodel import Session, SQLModel, create_engine

from ..core.config import settings


messenger_engine = create_engine(settings.MESSENGER_DATABASE_URL, echo=False)


def get_messenger_session():
    with Session(messenger_engine) as session:
        yield session


def init_messenger_db():
    from ..models.bank import Bank  # noqa: F401
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
