from fastapi import APIRouter

from .routers import campaign, user, webhook

master_router = APIRouter()

master_router.include_router(campaign.router)
master_router.include_router(user.router)
master_router.include_router(webhook.router)