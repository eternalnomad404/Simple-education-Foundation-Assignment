from enum import Enum
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.campaign import CampaignCreate, CampaignUpdate
from app.db.models import AuditAction, AutidEvent, Campaign, User

from .base import BaseService


class CampaignService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(Campaign, session)

    # Get all campaigns
    async def get_all_campaigns(self) -> list[Campaign] | None:

        campaigns = await self._get_all()
        return campaigns

    # Get a Campaign by ID
    async def get_campaign(
        self,
        id: UUID,
    ):
        campaign = await self._get(id)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign with given ID does not exist",
            )

        return campaign

    # Create/add a campaign
    async def create_campaign(
        self,
        data: CampaignCreate,
        user: User,
    ) -> Campaign:
        new_campaign = Campaign(**data.model_dump())
        if not new_campaign.name or not new_campaign.status:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign name and status are required",
            )

        await self._create(new_campaign)

        audit_event = AutidEvent(
            entity_type="campaign",
            entity_id=new_campaign.id,
            action=AuditAction.CREATED,
            actor_id=user.id,
            changes={
                "name": {
                    "from": None,
                    "to": new_campaign.name,
                },
                "description": {
                    "from": None,
                    "to": new_campaign.description,
                },
                "status": {
                    "from": None,
                    "to": new_campaign.status.value,
                },
                "status_remark": {
                    "from": None,
                    "to": new_campaign.status_remark,
                },
            },
        )

        await self._create(audit_event)

        return new_campaign

    async def update_campaign(
        self,
        id: UUID,
        data: CampaignUpdate,
        user: User,
    ) -> Campaign:
        campaign = await self._get(id)

        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign with given ID does not exist",
            )

        campaign_update = data.model_dump(exclude_none=True)

        changes = {}

        for field, new_value in campaign_update.items():
            old_value = getattr(campaign, field)

            if old_value != new_value:
                changes[field] = {
                    "from": old_value.value if isinstance(old_value, Enum) else old_value,
                    "to": new_value.value if isinstance(new_value, Enum) else new_value,
                }

        campaign.sqlmodel_update(campaign_update)

        await self._update(campaign)

        if changes:
            audit_event = AutidEvent(
                entity_type="campaign",
                entity_id=campaign.id,
                action=AuditAction.UPDATED,
                actor_id=user.id,
                changes=changes,
            )

            await self._create(audit_event)

        return campaign

    async def delete_campaign(
        self,
        id: UUID,
        user: User,
    ):
        campaign = await self.get_campaign(id)

        campaign_name = campaign.name

        changes = {
            "name": {
                "from": campaign.name,
                "to": None,
            },
            "description": {
                "from": campaign.description,
                "to": None,
            },
            "status": {
                "from": campaign.status.value if campaign.status else None,
                "to": None,
            },
            "status_remark": {
                "from": campaign.status_remark,
                "to": None,
            },
        }

        audit_event = AutidEvent(
            entity_type="campaign",
            entity_id=campaign.id,
            action=AuditAction.DELETED,
            actor_id=user.id,
            changes=changes,
        )

        await self._create(audit_event)
        await self._delete(campaign)

        return {"detail": f"Campaign Deleted - {campaign_name}"}
