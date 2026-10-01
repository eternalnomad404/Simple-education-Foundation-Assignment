"""Test 2.1 - POST /webhook/status is protected by the webhook secret."""

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MessageEvent
from tests.factories import create_outbound_message

STATUS_PAYLOAD = {
    "provider": "fake_provider",
    "provider_event_id": "event_auth_001",
    "provider_message_id": "msg_test_001",
    "status": "delivered",
    "event_timestamp": "2026-09-29T19:00:00",
}


async def _event_count(session: AsyncSession) -> int:
    return await session.scalar(select(func.count()).select_from(MessageEvent))


async def test_status_webhook_rejects_missing_secret(
    client: AsyncClient,
    db_session: AsyncSession,
):
    await create_outbound_message(db_session)

    response = await client.post("/webhook/status", json=STATUS_PAYLOAD)

    assert response.status_code == 401
    assert await _event_count(db_session) == 0


async def test_status_webhook_rejects_incorrect_secret(
    client: AsyncClient,
    db_session: AsyncSession,
):
    await create_outbound_message(db_session)

    response = await client.post(
        "/webhook/status",
        json=STATUS_PAYLOAD,
        headers={"X-Webhook-Secret": "not-the-secret"},
    )

    assert response.status_code == 401
    assert await _event_count(db_session) == 0


async def test_status_webhook_accepts_correct_secret(
    client: AsyncClient,
    db_session: AsyncSession,
    webhook_headers: dict[str, str],
):
    await create_outbound_message(db_session)

    response = await client.post(
        "/webhook/status",
        json=STATUS_PAYLOAD,
        headers=webhook_headers,
    )

    assert response.status_code == 200
    assert await _event_count(db_session) == 1
