import asyncio

from sqlmodel import select

from app.db.models import Campaign
from app.db.session import get_session
from scripts.seeds.cohort import seed_cohort
from scripts.seeds.message import seed_outbound_message
from scripts.seeds.teacher import seed_teachers


async def seed():
    async for session in get_session():
        cohort = await seed_cohort(session)

        teachers = await seed_teachers(
            session=session,
            cohort_id=cohort.id,
        )

        result = await session.execute(
            select(Campaign).where(
                Campaign.name == "Weekly Teacher Check-in"
            )
        )

        campaign = result.scalar_one_or_none()

        if not campaign:
            raise RuntimeError(
                'Required campaign "Weekly Teacher Check-in" does not exist. '
                "Create it through the Campaign API before running the seed."
            )

        await seed_outbound_message(
            session=session,
            teacher_id=teachers[0].id,
            campaign_id=campaign.id,
        )

        await session.commit()

        print("Seed data created successfully.")


if __name__ == "__main__":
    asyncio.run(seed())