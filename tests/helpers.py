"""Small helpers shared by the status webhook tests."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, MessageEvent


def status_payload(
    provider_event_id: str,
    status: str,
    event_timestamp: str,
    provider_message_id: str = "msg_test_001",
) -> dict[str, str]:
    return {
        "provider": "fake_provider",
        "provider_event_id": provider_event_id,
        "provider_message_id": provider_message_id,
        "status": status,
        "event_timestamp": event_timestamp,
    }


async def stored_events(session: AsyncSession) -> list[MessageEvent]:
    result = await session.scalars(select(MessageEvent))
    return list(result.all())


async def reload_message(session: AsyncSession, message: Message) -> Message:
    return await session.scalar(
        select(Message)
        .where(Message.id == message.id)
        .execution_options(populate_existing=True)
    )
