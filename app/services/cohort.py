from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Cohort

from .base import BaseService


class CohortService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(Cohort, session)

    # Get all cohorts
    async def get_all_cohorts(self) -> list[Cohort]:
        return await self._get_all()
