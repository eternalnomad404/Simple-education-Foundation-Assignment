# syntax=docker/dockerfile:1

# ---- base: Python, uv and the runtime dependencies -------------------------
FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Dependencies are installed before the source is copied, so this layer is
# reused until pyproject.toml or uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY migrations ./migrations
COPY app ./app
COPY scripts ./scripts

RUN useradd --system --no-create-home appuser


# ---- test: adds the development dependencies and the test suite ------------
FROM base AS test

RUN uv sync --frozen --no-install-project
COPY tests ./tests

USER appuser

CMD ["pytest", "-p", "no:cacheprovider"]


# ---- runtime: the image that serves the API --------------------------------
FROM base AS runtime

USER appuser

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
