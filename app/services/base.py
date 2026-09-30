

from uuid import UUID

from sqlalchemy.ext. asyncio import AsyncSession
from sqlmodel import SQLModel, select


class BaseService:
    def __init__(self, model: SQLModel, session: AsyncSession,):
        # Get database session to perform database ops
        self.model = model
        self.session = session

    async def _get_all(self):
        entities = await self.session.scalars(select(self.model))

        return entities.all()

    async def _get(self, id: UUID):
        return await self.session.get(self.model, id)

    async def _save(self, entity: SQLModel):
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)

        return entity

    async def _create(self, entity: SQLModel):
        return await self._save(entity)

    async def _update(self, entity: SQLModel):
        return await self._save(entity)

    async def _delete(self, entity: SQLModel):
        await self.session.delete(entity)
        await self.session.commit()