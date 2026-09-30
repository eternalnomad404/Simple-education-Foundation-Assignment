from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# from sqlmodel import SQLModel
from app.config import db_settings

engine = create_async_engine(
    # database type/ Dialect
    url = db_settings.POSTGRES_URL,

    # log sql queries
    echo = True
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False   
)

# Creates an async database session, yields it for use during the request,
# and automatically closes the session when the request is finished.
async def get_session():

    async with async_session() as session:
        yield session
