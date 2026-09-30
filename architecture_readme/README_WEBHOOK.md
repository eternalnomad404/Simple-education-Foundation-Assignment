# Webhook and Message Processing

This document explains the webhook and message-processing portion of the take-home assignment: what is implemented, why some parts are simulated, and how the same design would connect to a real messaging provider in production.

## Purpose

The application models communication between the system and teachers.

There are two message directions:

```text
OUTBOUND
Our application → Messaging provider → Teacher

INBOUND
Teacher → Messaging provider → Our application
```

The take-home scaffold focuses on receiving and processing provider webhooks rather than implementing a complete external messaging integration.

This is intentional. A real provider would introduce provider-specific APIs, credentials, SDKs, delivery behavior, and infrastructure that are not necessary for evaluating the backend concepts covered by this assignment.

## Message Model

A `Message` represents the message itself.

Important fields include:

```text
provider
provider_message_id
content
direction
teacher_id
campaign_id
created_at
status_updated_at
```

`direction` distinguishes inbound and outbound messages.

Outbound messages are associated with a campaign. Inbound messages currently have `campaign_id = null`.

This is deliberate: an inbound provider webhook does not necessarily tell us which campaign the teacher is replying to. Determining conversational or campaign attribution would require additional product rules and provider-specific context, which is outside the current scope.

## Message Events

Message delivery state is stored separately in `MessageEvent`.

A message can therefore have a timeline such as:

```text
Message
  │
  ├── SENT
  ├── DELIVERED
  └── READ
```

Each event stores:

```text
status
provider
provider_event_id
event_timestamp
received_at
raw_payload
message_id
```

`event_timestamp` is the time reported by the provider.

`received_at` is when our application received the webhook.

`raw_payload` stores the validated and normalised webhook payload received by the application. It is generated from the parsed webhook schema rather than preserving the original HTTP request body exactly.

The message's `current_status` is derived from its chronologically ordered event timeline rather than stored as another independent status value.

## Why Is an Outbound Message Seeded?

The scaffold does not currently implement message sending.

However, a status webhook only makes sense if the system already knows about the outbound message whose status is being reported.

For example, a provider may send:

```json
{
  "provider": "fake_provider",
  "provider_event_id": "event_001",
  "provider_message_id": "msg_out_001",
  "status": "delivered",
  "event_timestamp": "2026-09-29T19:00:00"
}
```

Before processing this event, our database must already contain the message identified by:

```text
provider = fake_provider
provider_message_id = msg_out_001
```

For the assignment, that outbound message is created through seed data.

The seed is therefore not intended to represent how messages would normally enter the system. It provides the minimum existing state required to exercise the webhook lifecycle without requiring a real messaging provider.

## What Would Happen in a Real System?

In production, the seed would be replaced by an outbound messaging service.

Conceptually:

```text
Campaign / Application Logic
          │
          ▼
Outbound Message Service
          │
          ├── Create/prepare message
          │
          ▼
Messaging Provider API
          │
          ├── Provider accepts message
          └── Returns provider_message_id
          │
          ▼
Store Message
          │
          ├── direction = OUTBOUND
          ├── campaign_id
          ├── teacher_id
          └── provider_message_id
          │
          ▼
Provider delivers message
          │
          ▼
Provider calls our status webhook
          │
          ▼
MessageEvent stored
```

The exact order of persistence and provider calls may vary depending on the delivery architecture and reliability requirements, but the important point is that the outbound service would create the message record and retain the provider's message identifier.

That identifier is what later allows webhook events to be correlated with the correct internal message.

The seeded outbound message stands in for that missing outbound-service step.

## Incoming Message Webhook

The application exposes an incoming-message webhook.

Conceptually:

```text
Teacher
   │
   ▼
Messaging Provider
   │
   ▼
POST /webhook/message
   │
   ├── Identify teacher by sender phone
   │
   ├── Unknown teacher → 404
   │
   ▼
Create Message
   │
   ├── direction = INBOUND
   ├── teacher_id = matched teacher
   └── campaign_id = null
```

The current implementation identifies the teacher using the sender phone number supplied by the fake provider.

In a real provider integration, this webhook schema would normally be produced by a provider adapter that translates the provider-specific payload into the application's internal message representation.

## Message Status Webhook

The application also exposes:

```text
POST /webhook/status
```

A status event is processed using both:

```text
provider
provider_message_id
```

This locates the existing message that the external provider is referring to.

The processing flow is:

```text
Status webhook
      │
      ▼
Find Message
      │
      ├── Not found → 404
      │
      ▼
Check provider_event_id
      │
      ├── Already processed → return existing event
      │
      ▼
Create MessageEvent
      │
      ├── Store provider timestamp
      ├── Store local receipt timestamp
      ├── Preserve raw payload
      └── Associate with Message
```

## Idempotency

Webhook providers may retry events.

Receiving the same webhook twice must therefore not create duplicate status events.

`provider_event_id` is unique, and the service checks whether an event has already been processed before creating another `MessageEvent`.

For example:

```text
event_001 arrives
    → MessageEvent created

event_001 arrives again
    → Existing MessageEvent returned
    → No duplicate row created
```

The database uniqueness constraint provides an additional integrity guarantee around the provider event identifier.

## Out-of-Order Events

Webhook events are not guaranteed to arrive in chronological order.

For example, the application could receive:

```text
READ      @ 19:05
DELIVERED @ 19:02
```

in that arrival order.

The older `DELIVERED` event is still valid and should be stored, but it should not make the message appear to have moved backwards in time.

The `Message.timeline` relationship is therefore ordered by `MessageEvent.event_timestamp`.

The derived `current_status` uses the latest event in that chronological timeline.

`status_updated_at` is also only moved forward when the incoming event timestamp is newer than the currently stored timestamp.

This allows the event history to remain complete even when provider delivery is delayed or reordered.

## Webhook Authentication

Webhook endpoints do not use the application's user JWT authentication.

A webhook request represents an external messaging provider, not a logged-in application user.

For this assignment, both webhook endpoints require:

```text
X-Webhook-Secret
```

The supplied value must match `WEBHOOK_SECRET` from the application environment.

Requests with an incorrect secret are rejected.

This is intentionally a simple shared-secret mechanism suitable for the fake-provider scope.

A production provider integration may instead use provider-specific verification mechanisms such as signed payloads, HMAC signatures, verification tokens, IP restrictions, or other authentication mechanisms supported by that provider.

## Fake Provider vs. Production Provider

The current webhook schemas are intentionally provider-neutral enough for the assignment:

```text
IncomingMessageWebhook
MessageStatusWebhook
```

A production system would normally introduce a provider integration boundary:

```text
WhatsApp / SMS / Other Provider
             │
             ▼
Provider-specific payload
             │
             ▼
Provider Adapter
             │
             ▼
Internal message/event representation
             │
             ▼
Message processing services
```

This keeps provider-specific payload formats and authentication rules from spreading through the core application.

The current fake provider effectively skips the external API and adapter layers so that the assignment can focus on persistence, webhook processing, event history, idempotency, and service design.

## Seed Data

Seed data currently provides the minimum domain state required to exercise the webhook flow:

```text
Cohort
  │
  └── Teacher

Campaign
  │
  └── Outbound Message
```

Cohorts and teachers are development fixtures.

Campaigns are created through the application API rather than seeded because campaign creation is an authenticated application operation and produces audit history.

The outbound message seed then associates a teacher with an existing campaign and gives the message a known fake-provider identifier such as:

```text
provider = fake_provider
provider_message_id = msg_out_001
```

This allows status webhooks to be tested immediately.

## Current Scope Boundary

The webhook/message scaffold currently demonstrates:

- inbound message ingestion;
- teacher lookup for incoming messages;
- outbound message representation;
- message-to-campaign association;
- provider message correlation;
- message status events;
- chronological event timelines;
- duplicate webhook handling;
- out-of-order event handling;
- storage of validated webhook payloads; and
- webhook authentication.

It intentionally does **not** implement a complete outbound messaging provider client.

In a real deployment, that missing piece would be a service responsible for sending outbound messages through the configured provider, capturing the provider's returned message identifier, and persisting the message so that subsequent webhook events can be correlated and processed by the infrastructure already represented here.
