from fastapi import APIRouter

from app.api.api_tag import APITag
from app.api.dependencies import CohortServiceDep
from app.api.schemas.cohort import CohortRead
from app.db.models import Cohort

router = APIRouter(prefix="/cohort", tags=[APITag.COHORT])


@router.get("/all", response_model=list[CohortRead])
async def get_all_cohorts(service: CohortServiceDep) -> list[Cohort]:
    return await service.get_all_cohorts()
