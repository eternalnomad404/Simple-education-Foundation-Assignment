# Backend Developer Take-Home Assignment

This repository contains a small FastAPI backend used as the starting
point for the backend developer take-home assignment.

The application is intentionally limited in scope. It is not intended to
represent a complete production messaging platform. Your task will be to
understand the existing implementation and work within it for the
assignment described separately.

## 1. What is in the repository

The application includes:

-   a FastAPI API
-   PostgreSQL persistence using SQLModel / SQLAlchemy
-   Alembic database migrations
-   JWT-based user authentication
-   Redis-backed token blacklisting
-   campaign management
-   cohorts and teachers
-   inbound and outbound messages
-   message delivery/status events
-   webhook endpoints for simulated messaging-provider callbacks
-   audit events
-   seed data for exercising the messaging flow
-   a pytest test suite
-   a Docker Compose setup that runs the application and its dependencies

More detailed architecture documentation is available in:

``` text
architecture_readme/
├── README_API.md
└── README_WEBHOOK.md
```

`README_API.md` explains the regular API and authentication flows.

`README_WEBHOOK.md` explains the messaging and webhook flow.

`REPOSITORY_GUIDE.md` provides a broader walkthrough of the repository
structure and the responsibility of the main modules.

## 2. Prerequisites

-   Docker with Docker Compose (Docker Desktop includes both)

Nothing else needs to be installed. Python, PostgreSQL and Redis all run
in containers.

## 3. Configure the environment

Create your local `.env` file from the provided `.env.example` file.

On macOS/Linux:

``` bash
cp .env.example .env
```

On Windows PowerShell:

``` powershell
Copy-Item .env.example .env
```

The defaults in `.env.example` are enough to run the application on your
own machine. The file explains each value. Change the database password,
`JWT_SECRET` and `WEBHOOK_SECRET` before using it anywhere else.

`WEBHOOK_SECRET` is the value webhook requests must send in the
`X-Webhook-Secret` header.

Do not commit your local `.env` file.

## 4. Start the application

``` bash
docker compose up --build
```

This single command:

1.  starts PostgreSQL and Redis and waits until both are ready,
2.  applies all Alembic migrations (the `migrate` service, which then
    exits),
3.  starts the API once the migrations have succeeded.

The API is then available at:

-   http://127.0.0.1:8000/ - health check
-   http://127.0.0.1:8000/docs - API documentation
-   http://127.0.0.1:8000/scalar - Scalar API documentation

If port 8000 is already in use, set `APP_PORT` in `.env` to another port.

PostgreSQL and Redis are not published on the host, so they cannot clash
with a PostgreSQL or Redis you already have running.

Useful commands:

``` bash
docker compose up --build -d     # run in the background
docker compose logs -f api       # follow the API logs
docker compose down              # stop, keeping the database
docker compose down -v           # stop and delete the database
```

The database lives in a Docker volume. Setting a different
`POSTGRES_PASSWORD` after the first start does not change the password of
the existing database; run `docker compose down -v` to start again from an
empty one.

## 5. Create the initial API data

Before running the seed script, create the campaign used by the seeded
messaging example.

Using the existing authentication and campaign endpoints:

1.  Register a user.
2.  Log in and obtain an access token. When using the OAuth2 login form,
    enter the user's email address in the `username` field.
3.  Authorize your requests using that token.
4.  Create a campaign with the exact name:

``` text
Weekly Teacher Check-in
```

Create this campaign once.

The campaign is created through the API rather than by the seed script
so that the existing authenticated campaign and audit flow is exercised.

## 6. Run the seed

Once the campaign exists, and with the application running:

``` bash
docker compose exec api python -m scripts.seed
```

The seed creates/reuses the sample cohort, teachers and outbound message
required for exercising the webhook flow.

The seed is safe to run again against the same initialized database;
existing seed records are reused rather than inserted again.

If the required `Weekly Teacher Check-in` campaign does not exist, the
seed will stop with an explanatory error.

## 7. Exercise the application

### Webhooks

The repository contains webhook endpoints representing callbacks from a
messaging provider.

Webhook requests are authenticated separately from user-facing API
requests. Send the configured webhook secret using:

``` text
X-Webhook-Secret: <your configured WEBHOOK_SECRET>
```

A request with a missing or incorrect secret is rejected with `401`.

The existing webhook surface includes:

``` text
POST /webhook/message
POST /webhook/status
```

The seeded outbound message can be used to exercise the status webhook:

``` bash
curl -X POST http://127.0.0.1:8000/webhook/status \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: communicator_key" \
  -d '{
        "provider": "fake_provider",
        "provider_event_id": "event_001",
        "provider_message_id": "msg_out_001",
        "status": "delivered",
        "event_timestamp": "2026-09-29T19:00:00Z"
      }'
```

Refer to:

``` text
architecture_readme/README_WEBHOOK.md
```

for the webhook schemas and an explanation of the message lifecycle.

### Teachers

An authenticated user can create a teacher:

``` text
GET  /cohort/all     list cohorts, to find the cohort id (public)
POST /teacher/       create a teacher (requires a logged-in user)
```

``` json
{
  "name": "Meera",
  "phone": "+91 98765 43299",
  "cohort_id": "<id from GET /cohort/all>"
}
```

The phone number is stored as digits only (`919876543299`), must be 8 to
15 digits including the country code, and must not already belong to
another teacher. Cohorts are still created by the seed script.

## 8. Run the tests

``` bash
docker compose run --rm --build tests
```

This is the only command needed; it starts PostgreSQL if it is not
already running.

The tests run the real application against a real PostgreSQL server. They
use their own database, `communicator_test`, which the test run creates
and migrates itself. Your development data is never read or changed, and
the tests do not depend on the seed script.

### Running without Docker

The application and tests can also be run directly, which is convenient
while developing. This needs Python 3.12, [`uv`](https://docs.astral.sh/uv/),
and a PostgreSQL and Redis you provide, with `POSTGRES_SERVER`,
`POSTGRES_PORT`, `REDIS_HOST` and `REDIST_PORT` in `.env` pointing at
them.

``` bash
uv sync
uv run alembic upgrade head
uv run fastapi dev app/main.py
uv run python -m scripts.seed
uv run pytest
```

## 9. Suggested reading order

Once the application is running, a useful order for understanding the
repository is:

``` text
README.md
    ↓
REPOSITORY_GUIDE.md
    ↓
architecture_readme/README_API.md
architecture_readme/README_WEBHOOK.md
    ↓
application code
```

You are expected to understand the relevant existing code before making
changes for the assignment, but you are not expected to redesign or
productionise unrelated parts of the application.

## 10. Database changes

If your work requires a database schema change, create a new Alembic
migration rather than modifying an existing migration.

Review generated migrations before applying them.

New migrations are applied the next time the application is started with
`docker compose up --build`. To apply them without restarting:

``` bash
docker compose run --rm --build migrate
```

## 11. Scope

This repository is deliberately a small assessment scaffold.

It contains enough application structure to provide realistic backend
problems, but it does not attempt to implement every feature, validation
rule, failure mode or operational concern that would exist in a
production messaging system.

Unless an assignment task specifically requires it, you do not need to fix
unrelated issues or add production features outside the requested scope.
If you do notice something that looks like a correctness problem rather than
a deliberate scope limitation, note it, whether you act on it is a separate judgement.
