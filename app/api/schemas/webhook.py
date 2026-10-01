from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from app.db.models import MessageStatus


def _to_naive_utc(value: datetime) -> datetime:
    """Convert a timestamp carrying a timezone to UTC without one.

    The database columns hold timestamps without a timezone. A value that
    arrives without one is taken to already be in UTC.
    """
    if value.tzinfo is None:
        return value

    return value.astimezone(timezone.utc).replace(tzinfo=None)


ProviderTimestamp = Annotated[datetime, AfterValidator(_to_naive_utc)]


class IncomingMessageWebhook(BaseModel):
    provider: str
    provider_message_id: str
    sender_phone: str
    content: str
    event_timestamp: ProviderTimestamp


class MessageStatusWebhook(BaseModel):
    provider: str
    provider_event_id: str
    provider_message_id: str
    status: MessageStatus
    event_timestamp: ProviderTimestamp
