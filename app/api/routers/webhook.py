from fastapi import APIRouter, Depends

from app.api.dependencies import WebhookServiceDep, verify_webhook_secret
from app.api.schemas.webhook import (
    IncomingMessageWebhook,
    MessageStatusWebhook,
)

router = APIRouter(
    prefix="/webhook",
    tags=["Webhook"],
    dependencies=[Depends(verify_webhook_secret)],
)


@router.post("/message")
async def incoming_message(
    data: IncomingMessageWebhook,
    service: WebhookServiceDep,
):
    return await service.process_incoming_message(data)


@router.post("/status")
async def message_status(
    data: MessageStatusWebhook,
    service: WebhookServiceDep,
):
    return await service.process_message_status(data)