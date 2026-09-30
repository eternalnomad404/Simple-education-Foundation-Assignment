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

Before starting, make sure you have the following installed:

-   Python 3.12
-   `uv`
-   PostgreSQL
-   Redis

The project was developed using PostgreSQL and Redis locally.

## 3. Install the project

Clone the repository and move into the project directory.

Install the project dependencies:

``` bash
uv sync
```

## 4. Environment configuration

Create your local `.env` file from the provided `.env.example` file.

On macOS/Linux:

``` bash
cp .env.example .env
```

On Windows PowerShell:

``` powershell
Copy-Item .env.example .env
```

Update the values in `.env` for your local PostgreSQL and Redis setup
where required.

The application also expects a webhook secret. The value configured for
`WEBHOOK_SECRET` is used to authenticate requests to the webhook
endpoints through the `X-Webhook-Secret` header.

Do not commit your local `.env` file.

## 5. Prepare PostgreSQL

Create an empty PostgreSQL database for the application and make sure
the database configuration in `.env` points to it.

Then apply all existing migrations:

``` bash
uv run alembic upgrade head
```

Alembic is responsible for creating the application schema. You do not
need to create the tables manually.

## 6. Start Redis

Make sure a Redis server is running using the host and port configured
in your `.env`.

Redis is used by the authentication flow for token blacklisting.

## 7. Start the API

Run the FastAPI application:

``` bash
fastapi dev app/main.py
```

Once the server is running, open the API documentation exposed by the
application.

Once the server is running, you can access the API documentation
at http://127.0.0.1:8000/docs or the Scalar documentation
at http://127.0.0.1:8000/scalar - Same is implemented in main.py

## 8. Verify the application

Before continuing, verify that:

1.  PostgreSQL is running.
2.  Redis is running.
3.  All Alembic migrations have completed successfully.
4.  The FastAPI application starts without errors.
5.  GET / responds successfully. (health endpoint)

At this point, the base application is running correctly.

## 9. Create the initial API data

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

## 10. Run the seed

Once the campaign exists, run:

``` bash
uv run python -m scripts.seed
```

The seed creates/reuses the sample cohort, teachers and outbound message
required for exercising the webhook flow.

The seed is safe to run again against the same initialized database;
existing seed records are reused rather than inserted again.

If the required `Weekly Teacher Check-in` campaign does not exist, the
seed will stop with an explanatory error.

## 11. Exercise the webhook flow

The repository contains webhook endpoints representing callbacks from a
messaging provider.

Webhook requests are authenticated separately from user-facing API
requests. Send the configured webhook secret using:

``` text
X-Webhook-Secret: <your configured WEBHOOK_SECRET>
```

The existing webhook surface includes:

``` text
POST /webhook/message
POST /webhook/status
```

The seeded outbound message can be used to exercise the status webhook.

Refer to:

``` text
architecture_readme/README_WEBHOOK.md
```

for the webhook schemas, an example status payload, and an
explanation of the message lifecycle.

## 12. Suggested reading order

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

## 13. Database changes

If your assignment work requires a database schema change, create a new
Alembic migration rather than modifying an existing migration.

Review generated migrations before applying them.

Apply new migrations with:

``` bash
uv run alembic upgrade head
```

## 14. Scope

This repository is deliberately a small assessment scaffold.

It contains enough application structure to provide realistic backend
problems, but it does not attempt to implement every feature, validation
rule, failure mode or operational concern that would exist in a
production messaging system.

Unless an assignment task specifically requires it, you do not need to fix
unrelated issues or add production features outside the requested scope.
If you do notice something that looks like a correctness problem rather than
a deliberate scope limitation, note it, whether you act on it is a separate judgement.
