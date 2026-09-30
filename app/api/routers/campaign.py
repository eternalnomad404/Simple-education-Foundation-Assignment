from uuid import UUID

from fastapi import APIRouter

from app.api.api_tag import APITag
from app.api.dependencies import CampaignServiceDep, UserAuthDep
from app.api.schemas.campaign import CampaignCreate, CampaignRead, CampaignUpdate
from app.db.models import Campaign

router = APIRouter(prefix="/campaign", tags=[APITag.CAMPAIGN])


@router.get("/all", response_model=list[CampaignRead])
async def get_all_campaigns(service: CampaignServiceDep) -> list[Campaign]:
    return await service.get_all_campaigns()


@router.get("/", response_model=CampaignRead)
async def get_campaign(
    id: UUID,
    service: CampaignServiceDep,
) -> Campaign:

    campaign = await service.get_campaign(id)

    return campaign


@router.post("/", response_model=CampaignRead)
async def create_campaign(
    data: CampaignCreate,
    user: UserAuthDep,
    service: CampaignServiceDep,
):
    return await service.create_campaign(data, user)


@router.patch("/", response_model=CampaignRead)
async def update_campaign(
    id: UUID,
    data: CampaignUpdate,
    user: UserAuthDep,
    service: CampaignServiceDep,
) -> Campaign:

    return await service.update_campaign(id, data, user)


@router.delete("/")
async def delete_campaign(
    id: UUID, service: CampaignServiceDep, user: UserAuthDep,
) -> dict[str, str]:

    return await service.delete_campaign(id, user)
