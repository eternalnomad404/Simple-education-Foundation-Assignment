"""
Shared test setup.

The tests run the real application against a real PostgreSQL database
(the models use PostgreSQL-only types, so SQLite is not an option).

- A dedicated test database is used, never the development one.
- Its schema is built by running the Alembic migrations.
- Every test starts from empty tables.
"""

import asyncio
import os

# The settings objects are created when app.config is first imported, and
# real environment variables win over the .env file. These must therefore
# be set before anything from the application is imported.
os.environ["POSTGRES_DB"] = os.environ.get("TEST_POSTGRES_DB", "communicator_test")
os.environ["WEBHOOK_SECRET"] = "test-webhook-secret"
os.environ["JWT_SECRET"] = "test-jwt-secret-used-only-by-the-test-suite"
os.environ["JWT_ALGORITHM"] = "HS256"

import asyncpg  # noqa: E402
import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402
from sqlmodel import SQLModel  # noqa: E402

from app.api.dependencies import get_current_user  # noqa: E402
from app.config import db_settings, webhook_settings  # noqa: E402
from app.db.models import User  # noqa: E402
from app.db.session import get_session  # noqa: E402
from app.main import app  # noqa: E402

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# NullPool: each test gets its own event loop, and a pooled connection
# cannot be reused across event loops.
test_engine = create_async_engine(db_settings.POSTGRES_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)


async def _create_database_if_missing() -> None:
    connection = await asyncpg.connect(
        user=db_settings.POSTGRES_USERNAME,
        password=db_settings.POSTGRES_PASSWORD,
        host=db_settings.POSTGRES_SERVER,
        port=db_settings.POSTGRES_PORT,
        database="postgres",
    )

    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            db_settings.POSTGRES_DB,
        )

        if not exists:
            await connection.execute(f'CREATE DATABASE "{db_settings.POSTGRES_DB}"')
    finally:
        await connection.close()


@pytest.fixture(scope="session", autouse=True)
def prepare_database():
    # Every test empties all tables, so refuse to run against anything
    # that is not clearly a test database.
    if not db_settings.POSTGRES_DB.endswith("_test"):
        raise RuntimeError(
            f'Refusing to run tests against "{db_settings.POSTGRES_DB}": '
            'the test database name must end with "_test".'
        )

    asyncio.run(_create_database_if_missing())

    # Build the schema the same way a real deployment does.
    command.upgrade(Config(os.path.join(ROOT_DIR, "alembic.ini")), "head")


@pytest_asyncio.fixture(autouse=True)
async def clean_tables(prepare_database):
    tables = ", ".join(f'"{table.name}"' for table in SQLModel.metadata.sorted_tables)

    async with test_engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE TABLE {tables} CASCADE"))


async def _get_test_session():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_session] = _get_test_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def db_session():
    """A session separate from the one the request used.

    Reading through it shows what was actually committed to the database.
    """
    async with TestSession() as session:
        yield session


@pytest.fixture
def webhook_headers() -> dict[str, str]:
    return {"X-Webhook-Secret": webhook_settings.WEBHOOK_SECRET}


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    user = User(
        name="Test User",
        email="test.user@example.com",
        password_hash="not-a-real-hash",
    )

    db_session.add(user)
    await db_session.commit()

    return user


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, user: User):
    """A client whose requests are treated as coming from `user`.

    Token decoding and the Redis blacklist are bypassed, so the suite
    needs PostgreSQL only. Tests that check the endpoint is protected use
    the plain `client`, which goes through the real authentication.
    """

    async def _current_user() -> User:
        return user

    app.dependency_overrides[get_current_user] = _current_user

    yield client
