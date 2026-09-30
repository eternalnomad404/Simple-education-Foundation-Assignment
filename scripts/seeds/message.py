from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, MessageDirection


async def seed_outbound_message(
    session: AsyncSession,
    teacher_id: UUID,
    campaign_id: UUID,
) -> Message:
    result = await session.execute(
        select(Message).where(
            Message.provider == "fake_provider",
            Message.provider_message_id == "msg_out_001",
        )
    )

    message = result.scalar_one_or_none()

    if message:
        return message

    message = Message(
        provider="fake_provider",
        provider_message_id="msg_out_001",
        content="How did your classroom activity go this week?",
        direction=MessageDirection.OUTBOUND,
        teacher_id=teacher_id,
        campaign_id=campaign_id,
    )

    session.add(message)
    await session.flush()

    return message