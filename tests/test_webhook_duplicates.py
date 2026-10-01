"""Test 2.2 - a status event delivered more than once is stored once."""

import asyncio

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.factories import create_outbound_message
from tests.helpers import status_payload, stored_events


async def test_duplicate_status_event_is_stored_once(
    client: AsyncClient,
    db_session: AsyncSession,
    webhook_headers: dict[str, str],
):
    await create_outbound_message(db_session)
    payload = status_payload("event_dup_001", "delivered", "2026-09-29T19:00:00")

    first = await client.post("/webhook/status", json=payload, headers=webhook_headers)
    second = await client.post("/webhook/status", json=payload, headers=webhook_headers)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]

    events = await stored_events(db_session)

    assert len(events) == 1
    assert events[0].provider_event_id == "event_dup_001"


async def test_duplicate_status_events_arriving_together_are_stored_once(
    client: AsyncClient,
    db_session: AsyncSession,
    webhook_headers: dict[str, str],
):
    """A provider retry can overlap with the original delivery."""
    await create_outbound_message(db_session)
    payload = status_payload("event_dup_002", "delivered", "2026-09-29T19:00:00")

    responses = await asyncio.gather(
        *[
            client.post("/webhook/status", json=payload, headers=webhook_headers)
            for _ in range(5)
        ]
    )

    assert [response.status_code for response in responses] == [200] * 5
    assert len({response.json()["id"] for response in responses}) == 1
    assert len(await stored_events(db_session)) == 1
