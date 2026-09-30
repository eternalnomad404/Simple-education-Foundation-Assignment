# from uuid import UUID

from datetime import datetime, timezone

from redis.asyncio import Redis

from app.config import db_settings

_token_blacklist = Redis(
    host=db_settings.REDIS_HOST, port=db_settings.REDIST_PORT, db=0
)


async def add_jti_to_blacklist(jti: str, exp: int):

    now = datetime.now(timezone.utc).timestamp()

    ttl = max(int(exp - now), 1)
    
    await _token_blacklist.set(
        jti,
        "blacklisted",
        ex=ttl,
    )


async def is_jti_blacklisted(jti: str) -> bool:
    return bool(await _token_blacklist.exists(jti))