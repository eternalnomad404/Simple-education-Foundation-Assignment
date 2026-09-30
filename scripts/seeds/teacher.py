from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Teacher


async def seed_teachers(
    session: AsyncSession,
    cohort_id,
) -> list[Teacher]:
    teacher_data = [
        {
            "name": "Aisha",
            "phone": "919876543210",
        },
        {
            "name": "Rahul",
            "phone": "919876543211",
        },
    ]

    teachers = []

    for data in teacher_data:
        result = await session.execute(
            select(Teacher).where(
                Teacher.phone == data["phone"]
            )
        )

        teacher = result.scalar_one_or_none()

        if not teacher:
            teacher = Teacher(
                name=data["name"],
                phone=data["phone"],
                cohort_id=cohort_id,
            )

            session.add(teacher)
            await session.flush()

        teachers.append(teacher)

    return teachers