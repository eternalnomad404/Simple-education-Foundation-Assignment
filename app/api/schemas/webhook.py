from datetime import datetime

from pydantic import BaseModel

from app.db.models import MessageStatus


class IncomingMessageWebhook(BaseModel):
    provider: str
    provider_message_id: str
    sender_phone: str
    content: str
    event_timestamp: datetime


class MessageStatusWebhook(BaseModel):
    provider: str
    provider_event_id: str
    provider_message_id: str
    status: MessageStatus
    event_timestamp: datetime