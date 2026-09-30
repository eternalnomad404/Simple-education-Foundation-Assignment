from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Cohort


async def seed_cohort(session: AsyncSession) -> Cohort:
    result = await session.execute(
        select(Cohort).where(
            Cohort.name == "Cohort A",
            Cohort.region == "Delhi",
        )
    )

    cohort = result.scalar_one_or_none()

    if cohort:
        return cohort

    cohort = Cohort(
        name="Cohort A",
        region="Delhi",
    )

    session.add(cohort)
    await session.flush()

    return cohort