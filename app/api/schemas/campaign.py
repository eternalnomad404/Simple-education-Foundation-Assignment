from uuid import UUID

from pydantic import BaseModel

from app.db.models import CampaignStatus


class BaseCampaign(BaseModel):
    name: str
    description: str | None = None
    status: CampaignStatus
    status_remark: str | None = None

class CampaignCreate(BaseCampaign):
    """Campaign Details to create campaign"""

class CampaignRead(BaseCampaign):
    id: UUID

class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: CampaignStatus | None = None
    status_remark: str | None = None