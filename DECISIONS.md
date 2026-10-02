# Decisions

This document covers what I decided for each task and why, followed by an
overall summary. Section 6 lists what I noticed in the existing
application.

Everything described as a behaviour of the application was observed by
running it, unless it says "from reading the code".

## 1. Task 1 - Getting the application running

The application ran end to end by following `README.md`: migrations, API,
seed, and both webhooks. These are the things that did not work as
documented, or cost time:

-   **Redis on Windows.** The README lists Redis as a prerequisite, but
    Redis has no native Windows build. I ran PostgreSQL and Redis in
    Docker. Worth a line in the prerequisites.
-   **`fastapi dev app/main.py`** is given without `uv run`. `uv sync`
    installs into `.venv` without activating it, so in a fresh shell the
    command as written does not use the project's environment. I used
    `uv run fastapi dev app/main.py`.
-   **The example status payload does not show the documented behaviour.**
    Sending the example from `README_WEBHOOK.md` to the seeded message
    stored the event, but the message's `status_updated_at` did not
    change. This is the bug described in section 2.3.
-   **`REDIST_PORT`.** The setting is spelled this way in `.env.example`
    and `app/config.py`. It works, but only if you copy the typo.
-   **`REPOSITORY_GUIDE.md` section 13** opens a code block that is never
    closed, so the rest of that section renders as code.
-   **`README.md` section 7** says "Once the server is running, open the
    API documentation" twice.
-   Environment-specific: ports 5432 and 6379 were already in use on my
    machine, so I used other ports. This is why the Compose setup in
    Task 4 does not publish the database or Redis ports.

## 2. Task 2 - Automated tests

Run with one command: `docker compose run --rm --build tests`.
There are 20 tests; the three required ones are in
`tests/test_webhook_auth.py`, `tests/test_webhook_duplicates.py` and
`tests/test_webhook_ordering.py`.

### How the tests get a database

-   **A real PostgreSQL server, not SQLite.** The models use JSONB,
    PostgreSQL UUID and enum types, and the behaviour under test depends
    on a unique constraint and row locking. SQLite would test a different
    system.
-   **A separate database, `communicator_test`.** `tests/conftest.py` sets
    `POSTGRES_DB` before the application is imported, because the settings
    are read at import time. The suite refuses to start if the database
    name does not end in `_test`, since every test empties all tables.
-   **Schema from the Alembic migrations**, not `create_all()`. The tests
    then run against the schema a deployment would actually have, and a
    broken migration fails the suite.
-   **Tables are emptied before each test.** The services call `commit()`
    themselves, so wrapping each test in a transaction and rolling it back
    would need extra machinery. Truncating is simple, and fast enough at
    this size.

### How the application's dependencies are handled

-   **Database session:** `get_session` is overridden to use a test engine
    with no connection pool. pytest gives each test its own event loop,
    and a pooled connection cannot be reused across loops.
-   **Assertions read through a second session**, not the one the request
    used, so they see what was committed.
-   **Authentication:** for the teacher tests, `get_current_user` is
    overridden to return a real user row. The test that the endpoint is
    protected uses the real authentication. The suite therefore needs no
    Redis. The cost is that token decoding and the blacklist are not
    covered by these tests.
-   **No seed data:** `tests/factories.py` creates the rows each test
    needs.

### 2.1 Webhook authentication

A wrong secret returned `401`, but a missing header returned `422`,
because the header was declared as a required parameter. Both are the
same failure, and a `422` describing the expected header is the wrong
answer to an unauthenticated caller. I changed it to return `401` in both
cases, and made the comparison constant-time.

### 2.2 Duplicate status events

Two sequential deliveries of the same event already worked. I added a
second test that sends five copies at the same time, and it failed: each
request passed the "does this event exist" check before any had been
stored, and the later inserts hit the unique constraint and returned
`500`. Providers retry on timeouts, so an overlapping retry is realistic.

The fix locks the message row (`SELECT ... FOR UPDATE`) while a status
event for it is processed. The second request waits, then finds the
stored event and returns it. I chose this over catching the constraint
error because it also makes the `status_updated_at` update below safe
when two different events for one message arrive together.

Not covered: the same `provider_event_id` arriving at the same moment for
two *different* messages. `provider_event_id` is unique across all
providers, which is itself questionable (see section 6).

### 2.3 Out-of-order status events

This test failed against the original code. `status_updated_at` starts as
the message's creation time and was only moved forward when an event was
newer than the stored value. An event with a provider timestamp earlier
than the row's creation time was never reflected.

This is not only a test artefact. `created_at` uses the server's local
clock without a timezone, while providers report UTC. On a server in
India, every event in the first five and a half hours after sending would
be ignored.

I changed it to the latest `event_timestamp` in the message's timeline.
That is the same rule `current_status` uses, so the two cannot disagree.
I kept the column instead of deriving the value on read, to avoid a
schema change.

While writing this test I found that a timestamp with a timezone, such as
`2026-09-29T19:05:00Z`, returned `500`. That is the normal format for a
real provider. Timestamps are now converted to UTC when the payload is
validated. One without a timezone is assumed to be UTC already.

## 3. Task 3 - Creating a teacher

`POST /teacher/`, following the campaign feature: a schema, a
`TeacherService` built on `BaseService`, a thin router, and a dependency.

Decisions the existing code did not answer:

-   **Unknown cohort returns `404`.** Without a check it is a foreign key
    error and a `500`. I used `404` because the webhooks already answer
    that way when something named in the request body does not exist.
-   **Phone numbers must be unique.** The incoming message webhook finds
    the teacher by phone and expects at most one match; with two it would
    fail. I added a unique constraint with a new migration, and a
    duplicate returns `409`. The service checks first for a clear error,
    and the constraint catches two requests arriving together (tested).
-   **Phone numbers are stored as digits only**, 8 to 15 of them
    (`+91 98765-43210` becomes `919876543210`). The webhook compares the
    stored string exactly, so one teacher must not be storable in two
    spellings. Digits-only is the format the seed data already uses.
-   **An audit event is recorded**, because campaign changes are audited
    and the audit table was designed to be generic. Unlike the campaign
    service, the teacher and its audit event are saved in one commit, so
    there cannot be one without the other.
-   **`201 Created`.** The campaign endpoint returns `200` on creation. I
    used the more accurate code for the new endpoint and left the existing
    one alone.
-   **The response is a dedicated schema** (`id`, `name`, `phone`,
    `cohort_id`), not the model with its cohort and messages attached.
-   **I added `GET /cohort/all`.** A teacher needs a cohort id, and there
    was no way to get one except by querying the database. It is public,
    like the campaign reads.

The migration fails if two existing teachers already share a phone
number. Choosing which row to keep is a data decision, so I did not
automate it.

## 4. Task 4 - Containerization

`docker compose up --build` starts PostgreSQL, Redis, runs the
migrations, then starts the API.

-   **Migrations run in a separate one-off service**, and the API waits
    for it to succeed. The alternative is a start-up script inside the API
    container. A separate service needs no shell script (which breaks when
    checked out on Windows with CRLF line endings), and stays correct if
    more than one API container is started.
-   **PostgreSQL and Redis are not published on the host.** Only the API
    needs to be reachable, and this avoids clashing with a database
    already running on the machine, which I hit myself.
-   **One Dockerfile with a `runtime` and a `test` stage.** The runtime
    image has no test code or development dependencies.
-   **Dependencies are installed from `uv.lock`**, so the image matches
    the versions the repository pins.
-   **The API runs as a non-root user**, with `fastapi run`, not the
    reloading `fastapi dev`.
-   **`.env.example` is rewritten** as plain `KEY=value` lines, a format I
    verified both Docker Compose and the application read, with defaults
    that work locally. Compose overrides the database and Redis host and
    port, so the same `.env` works inside and outside Docker.
-   **The seed is not run automatically.** It requires a campaign created
    through the API, which the documentation says is deliberate.

I verified this from a fresh clone on Windows: copy `.env.example`, run
the one command, and the API, migrations and tests all work.

## 5. Overall

### Approach

I ran the application before changing anything and tried the unhappy
paths by hand. That produced most of section 6. I then wrote the tests
against the documented behaviour, not the current behaviour, which is how
the bugs in 2.1 to 2.3 surfaced. I fixed only what was on the path the
tasks touch, one commit per fix, each with a test that failed before it.

I used an AI assistant (Claude Code) throughout.

### What I deliberately did not do

-   **Create, update or delete cohorts; update, delete or list
    teachers.** Not asked for. Cohort creation is the obvious next step,
    and brings its own questions (the seed assumes a cohort name and
    region are unique).
-   **Fix the issues in section 6 that are outside the tasks.** Each is a
    change to existing behaviour that deserves its own discussion.
-   **Rename `REDIST_PORT` and `AutidEvent`.** Renaming a setting breaks
    every existing `.env`.
-   **Normalise `sender_phone` in the incoming webhook.** The
    documentation assigns translating provider payloads to a provider
    adapter that does not exist yet. A provider sending `+91...` will not
    match until then.
-   **Store timestamps with a timezone.** The right fix for the clock
    issue, but it changes every timestamp column.
-   **Test login, logout and the Redis blacklist.** Outside the three
    required tests.
-   **CI.** There is no hosting context to target.

### Worth raising in the existing application

See section 6.

### With more time

-   Make duplicate incoming messages safe (unique constraint on provider
    and provider message id), since it currently leads to a `500`.
-   Add a unique constraint on user email.
-   Move all timestamps to timezone-aware UTC.
-   Make campaign changes and their audit events a single transaction.
-   Add cohort creation, and tests for the authentication flow.
-   Run the tests in CI on every push.

## 6. What I noticed in the existing application

### Correctness problems

Fixed on this branch, because the tasks touch them:

1.  `status_updated_at` ignores events older than the message row (2.3).
2.  Duplicate status events arriving together return `500` (2.2).
3.  A status timestamp with a timezone returns `500` (2.3).
4.  A missing webhook secret returns `422` instead of `401` (2.1).

Not fixed:

5.  **Duplicate incoming messages.** Sending the same
    `/webhook/message` payload twice stores two messages. After that, a
    status event for that provider message id returns `500`, because the
    lookup expects one row.
6.  **User emails are not unique.** Signing up twice with the same email
    succeeds and creates two users. Login then uses whichever the
    database returns first.
7.  **Deleting a campaign silently detaches its messages.** The delete
    succeeds and the outbound messages are left with no campaign, which
    the documentation says only applies to inbound messages.
8.  **Timestamps use the server's local clock with no timezone.** The
    same code wrote 18:06 on my machine and 12:48 in the container.
9.  **Campaign changes and their audit events are separate commits**
    (from reading the code). A failure in between leaves a change with no
    audit record.
10. **Authentication failures return `400`.** A logged-out token, an
    invalid token and a wrong password all return `400`; `401` is the
    expected code.
11. **The "add name to cohort" migration** adds a required column with no
    default (from reading the code). It fails on a database that already
    has cohorts.

### Could reasonably be designed differently

-   `provider_event_id` is unique on its own, not per provider. Two
    providers reusing an id would collide.
-   `PATCH /campaign/` drops `null` values, so a description or remark
    cannot be cleared once set.
-   The login response uses the key `type`; OAuth2 clients expect
    `token_type: bearer`.
-   Logout is a `GET` request although it changes state.
-   The database engine logs every SQL statement (`echo=True`).
-   `passlib` is no longer maintained and emits a deprecation warning
    under test.

### Intentional scope limits

The documentation says these are deliberate and I treated them that way:
no ownership checks on campaigns, no outbound sending, email verification
and `is_active` unused, a shared-secret header for webhooks, and inbound
messages not linked to a campaign.
