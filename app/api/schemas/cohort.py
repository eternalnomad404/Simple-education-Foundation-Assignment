from uuid import UUID

from pydantic import BaseModel


class CohortRead(BaseModel):
    id: UUID
    name: str
    region: str
