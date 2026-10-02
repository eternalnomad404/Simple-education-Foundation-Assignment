"""Task 3 - creating a teacher through the API."""

import asyncio
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditAction, AutidEvent, Teacher, User
from tests.factories import create_cohort, create_teacher


async def _teachers(session: AsyncSession) -> list[Teacher]:
    result = await session.scalars(select(Teacher))
    return list(result.all())


async def test_create_teacher_requires_authentication(
    client: AsyncClient,
    db_session: AsyncSession,
):
    cohort = await create_cohort(db_session)

    response = await client.post(
        "/teacher/",
        json={"name": "Aisha", "phone": "919876543210", "cohort_id": str(cohort.id)},
    )

    assert response.status_code == 401
    assert await _teachers(db_session) == []


async def test_create_teacher(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    user: User,
):
    cohort = await create_cohort(db_session)

    response = await authenticated_client.post(
        "/teacher/",
        json={"name": "  Aisha ", "phone": "919876543210", "cohort_id": str(cohort.id)},
    )

    assert response.status_code == 201

    teachers = await _teachers(db_session)

    assert len(teachers) == 1
    assert teachers[0].name == "Aisha"
    assert teachers[0].phone == "919876543210"
    assert teachers[0].cohort_id == cohort.id

    assert response.json() == {
        "id": str(teachers[0].id),
        "name": "Aisha",
        "phone": "919876543210",
        "cohort_id": str(cohort.id),
    }

    # The creation is recorded against the user who made it.
    audit_events = (await db_session.scalars(select(AutidEvent))).all()

    assert len(audit_events) == 1
    assert audit_events[0].entity_type == "teacher"
    assert audit_events[0].entity_id == teachers[0].id
    assert audit_events[0].action == AuditAction.CREATED
    assert audit_events[0].actor_id == user.id


async def test_create_teacher_stores_phone_as_digits_only(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
):
    cohort = await create_cohort(db_session)

    response = await authenticated_client.post(
        "/teacher/",
        json={
            "name": "Aisha",
            "phone": "+91 98765-43210",
            "cohort_id": str(cohort.id),
        },
    )

    assert response.status_code == 201
    assert response.json()["phone"] == "919876543210"


@pytest.mark.parametrize("phone", ["", "12345", "not-a-number", "1" * 16])
async def test_create_teacher_rejects_invalid_phone(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    phone: str,
):
    cohort = await create_cohort(db_session)

    response = await authenticated_client.post(
        "/teacher/",
        json={"name": "Aisha", "phone": phone, "cohort_id": str(cohort.id)},
    )

    assert response.status_code == 422
    assert await _teachers(db_session) == []


async def test_create_teacher_rejects_blank_name(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
):
    cohort = await create_cohort(db_session)

    response = await authenticated_client.post(
        "/teacher/",
        json={"name": "   ", "phone": "919876543210", "cohort_id": str(cohort.id)},
    )

    assert response.status_code == 422
    assert await _teachers(db_session) == []


async def test_create_teacher_with_unknown_cohort(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
):
    response = await authenticated_client.post(
        "/teacher/",
        json={"name": "Aisha", "phone": "919876543210", "cohort_id": str(uuid4())},
    )

    assert response.status_code == 404
    assert await _teachers(db_session) == []


async def test_create_teacher_with_phone_already_in_use(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
):
    cohort = await create_cohort(db_session)
    await create_teacher(db_session, cohort, phone="919876543210")

    # Same number, typed differently.
    response = await authenticated_client.post(
        "/teacher/",
        json={"name": "Rahul", "phone": "+91 9876543210", "cohort_id": str(cohort.id)},
    )

    assert response.status_code == 409
    assert len(await _teachers(db_session)) == 1
    assert (await db_session.scalars(select(AutidEvent))).all() == []


async def test_create_teacher_with_same_phone_at_the_same_time(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
):
    cohort = await create_cohort(db_session)
    payload = {"name": "Aisha", "phone": "919876543210", "cohort_id": str(cohort.id)}

    responses = await asyncio.gather(
        *[authenticated_client.post("/teacher/", json=payload) for _ in range(5)]
    )

    assert sorted(response.status_code for response in responses) == [
        201,
        409,
        409,
        409,
        409,
    ]
    assert len(await _teachers(db_session)) == 1
    assert len((await db_session.scalars(select(AutidEvent))).all()) == 1


async def test_incoming_message_is_matched_to_a_teacher_created_through_the_api(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
    webhook_headers: dict[str, str],
):
    cohort = await create_cohort(db_session)

    created = await authenticated_client.post(
        "/teacher/",
        json={"name": "Aisha", "phone": "+91 98765 43210", "cohort_id": str(cohort.id)},
    )

    response = await authenticated_client.post(
        "/webhook/message",
        json={
            "provider": "fake_provider",
            "provider_message_id": "msg_in_001",
            "sender_phone": "919876543210",
            "content": "It went well",
            "event_timestamp": "2026-09-29T19:10:00",
        },
        headers=webhook_headers,
    )

    assert response.status_code == 200
    assert response.json()["teacher_id"] == created.json()["id"]
