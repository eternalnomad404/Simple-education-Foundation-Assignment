"""Test 2.3 - status events that arrive out of chronological order."""

from datetime import datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MessageStatus
from tests.factories import create_outbound_message
from tests.helpers import reload_message, status_payload, stored_events


async def test_out_of_order_status_events(
    client: AsyncClient,
    db_session: AsyncSession,
    webhook_headers: dict[str, str],
):
    message = await create_outbound_message(db_session)

    # READ happened later but arrives first.
    read = await client.post(
        "/webhook/status",
        json=status_payload("event_read", "read", "2026-09-29T19:05:00"),
        headers=webhook_headers,
    )
    # DELIVERED happened earlier but arrives second.
    delivered = await client.post(
        "/webhook/status",
        json=status_payload("event_delivered", "delivered", "2026-09-29T19:02:00"),
        headers=webhook_headers,
    )

    assert read.status_code == 200
    assert delivered.status_code == 200

    events = await stored_events(db_session)

    assert {event.status for event in events} == {
        MessageStatus.READ,
        MessageStatus.DELIVERED,
    }

    message = await reload_message(db_session, message)

    assert [event.status for event in message.timeline] == [
        MessageStatus.DELIVERED,
        MessageStatus.READ,
    ]
    assert message.current_status == MessageStatus.READ
    assert message.status_updated_at == datetime(2026, 9, 29, 19, 5)


async def test_status_event_with_timezone_is_stored_as_utc(
    client: AsyncClient,
    db_session: AsyncSession,
    webhook_headers: dict[str, str],
):
    message = await create_outbound_message(db_session)

    # 00:35 at +05:30 is 19:05 UTC on the previous day.
    response = await client.post(
        "/webhook/status",
        json=status_payload("event_tz", "read", "2026-09-30T00:35:00+05:30"),
        headers=webhook_headers,
    )

    assert response.status_code == 200

    events = await stored_events(db_session)

    assert len(events) == 1
    assert events[0].event_timestamp == datetime(2026, 9, 29, 19, 5)

    message = await reload_message(db_session, message)

    assert message.status_updated_at == datetime(2026, 9, 29, 19, 5)
