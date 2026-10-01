"""Listing cohorts, so a client can find the cohort a teacher belongs to."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_cohort


async def test_get_all_cohorts(
    client: AsyncClient,
    db_session: AsyncSession,
):
    cohort = await create_cohort(db_session, name="Cohort A", region="Delhi")

    response = await client.get("/cohort/all")

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(cohort.id), "name": "Cohort A", "region": "Delhi"}
    ]
