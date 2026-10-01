"""Helpers that create the rows a test needs, without the seed script."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Campaign,
    CampaignStatus,
    Cohort,
    Message,
    MessageDirection,
    Teacher,
)


async def create_cohort(
    session: AsyncSession,
    name: str = "Test Cohort",
    region: str = "Test Region",
) -> Cohort:
    cohort = Cohort(name=name, region=region)

    session.add(cohort)
    await session.commit()

    return cohort


async def create_teacher(
    session: AsyncSession,
    cohort: Cohort,
    name: str = "Test Teacher",
    phone: str = "919000000001",
) -> Teacher:
    teacher = Teacher(name=name, phone=phone, cohort_id=cohort.id)

    session.add(teacher)
    await session.commit()

    return teacher


async def create_outbound_message(
    session: AsyncSession,
    provider: str = "fake_provider",
    provider_message_id: str = "msg_test_001",
) -> Message:
    """An outbound message, with the cohort, teacher and campaign it needs."""
    cohort = await create_cohort(session)
    teacher = await create_teacher(session, cohort)

    campaign = Campaign(name="Test Campaign", status=CampaignStatus.PLANNED)
    session.add(campaign)
    await session.commit()

    message = Message(
        provider=provider,
        provider_message_id=provider_message_id,
        content="How did your classroom activity go this week?",
        direction=MessageDirection.OUTBOUND,
        teacher_id=teacher.id,
        campaign_id=campaign.id,
    )

    session.add(message)
    await session.commit()

    return message
