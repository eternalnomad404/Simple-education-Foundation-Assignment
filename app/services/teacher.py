from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.teacher import TeacherCreate
from app.db.models import AuditAction, AutidEvent, Cohort, Teacher, User

from .base import BaseService


class TeacherService(BaseService):
    def __init__(
        self,
        session: AsyncSession,
    ):
        super().__init__(Teacher, session)

    async def _get_by_phone(self, phone: str) -> Teacher | None:
        return await self.session.scalar(
            select(Teacher).where(Teacher.phone == phone)
        )

    # Create/add a teacher
    async def create_teacher(
        self,
        data: TeacherCreate,
        user: User,
    ) -> Teacher:
        cohort = await self.session.get(Cohort, data.cohort_id)

        if not cohort:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cohort with given ID does not exist",
            )

        if await self._get_by_phone(data.phone):
            raise self._phone_taken()

        new_teacher = Teacher(**data.model_dump())

        self.session.add(new_teacher)

        try:
            # Sends the insert without committing, which assigns the id
            # the audit event needs.
            await self.session.flush()
        except IntegrityError:
            # Another request stored the same phone after the check above.
            # The unique constraint on teacher.phone is what catches it.
            await self.session.rollback()
            raise self._phone_taken() from None

        audit_event = AutidEvent(
            entity_type="teacher",
            entity_id=new_teacher.id,
            action=AuditAction.CREATED,
            actor_id=user.id,
            changes={
                "name": {
                    "from": None,
                    "to": new_teacher.name,
                },
                "phone": {
                    "from": None,
                    "to": new_teacher.phone,
                },
                "cohort_id": {
                    "from": None,
                    "to": str(new_teacher.cohort_id),
                },
            },
        )

        self.session.add(audit_event)

        # One commit: the teacher and its audit event are stored together
        # or not at all.
        await self.session.commit()
        await self.session.refresh(new_teacher)

        return new_teacher

    @staticmethod
    def _phone_taken() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teacher with this phone number already exists",
        )
