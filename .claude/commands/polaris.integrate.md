---
description: Add integrations to your application - Aptean Platform services, database, API, message queue, file processing, webhook, or real-time streaming.
---

<!-- integrate-dx-enhancements:v1 -->

## User Input

**Telemetry**: Run: `polaris telemetry record integrate --feature <slug> --phase start --agent claude`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Quick Mode

If user passes `--quick` or arguments contain "quick": Require only integration type and name (from arguments or ask once). Skip environment target question (default: all). Auto-detect project context. Generate config, client, tests, Docker Compose, and .env.example with defaults immediately.

## Goal

Add a production-ready integration to an existing application. Generates YAML config, typed client/adapter, health check, resilience patterns (retry, circuit breaker), and tests. All integration types follow the same consistent structure.

## Steps

### 1. Discovery

Detect project context: language/framework, existing integrations, config patterns, test framework.

**Smart skip rules (check before asking):**
- **Integration type**: If `$ARGUMENTS` already contains the integration type (e.g., the user typed `/polaris.integrate iam` or `/polaris.integrate postgresql`), do NOT ask for the type. Use the value from `$ARGUMENTS` directly.
- **Environment targets**: If the resolved integration type is any Aptean Platform service - IAM, Integration Platform, Intelligent Workflow, Intelligence Studio, CRM, or Pay - do NOT ask for environment targets. Silently default to all environments: local, dev, staging, production.

Ask the user only for questions not already resolved by the rules above:
- **Integration type** (skip if already in `$ARGUMENTS`):
  - **Aptean Platform**: IAM (OAuth2/OIDC), Integration Platform (REST+webhooks), Intelligent Workflow, Intelligence Studio (AI/ML), CRM (REST/GraphQL), Pay (payments)
  - **Database**: SQL Server, PostgreSQL, Azure SQL, Azure PostgreSQL Flex, MongoDB, MySQL, MariaDB, Redis, CosmosDB, DynamoDB, CockroachDB, Cassandra, Elasticsearch, SQLite, Oracle, Rocket U2
  - **REST/GraphQL API**, **Message Queue** (Kafka, RabbitMQ, Azure Service Bus, SQS/SNS, Pub/Sub, Redis Streams, NATS), **File/Batch** (SFTP, Azure Blob, S3, GCS, local), **Webhook** (inbound/outbound/both), **Real-time** (WebSocket, SSE, CDC, gRPC streaming), **Other**
- **Integration name**: kebab-case (e.g., `orders-api`, `inventory-db`)
- **Environment targets** (skip for Aptean Platform types - default to all): local, dev, staging, production

### 2. Generate Integration Config

Create `src/<app>/integrations/<name>/config.yaml` with standard structure:

```yaml
name: <name>
type: <type>
version: 1
connection:
  # Type-specific (see below)
auth:
  type: <none|api-key|oauth2|basic|cert|connection-string|managed-identity>
resilience:
  retry: {max_attempts: 3, backoff: exponential, base_delay_ms: 500}
  circuit_breaker: {failure_threshold: 5, reset_timeout_ms: 30000}
  timeout_ms: 5000
health: {enabled: true, interval_ms: 30000}
```

**Type-specific connection configs:**
- **Database**: engine, host, port, database, pool (min/max/idle). Auth: connection-string or managed-identity for cloud
- **Rocket U2**: variant (universe/unidata), account, access method (uniobjects/odbc/jdbc/rest)
- **REST/GraphQL API**: base_url, api_version. Auth: oauth2 with token_url/client_id/secret. Rate limiting
- **Message Queue**: broker type, broker_url, topics (name/direction/group_id), dead_letter config
- **File/Batch**: provider, host, container, path, poll_interval, chunk_size, file_patterns
- **Webhook**: direction (inbound/outbound/both), signature verification, idempotency, queue-backed processing
- **Real-time**: transport type, url, heartbeat, reconnect with backoff
- **Aptean Platform**: All authenticate via Aptean IAM (OAuth2). Use shared auth pattern with `${APTEAN_IAM_*}` env vars. Service-specific: Integration Platform has events/webhooks, Pay has payment webhooks, CRM/Workflow/Studio use standard REST

All credentials reference `${ENV_VAR}` placeholders, never hardcoded.

### 3. Generate Client/Adapter Code

Generate integration module:
```
src/<app>/integrations/<name>/
  __init__.py, config.py, client.py, models.py, health.py, retry.py, config.yaml
```

Client requirements by type:
- **Database**: Connection pool with explicit named parameters+comments, repository pattern (CRUD), parameterized queries (never string concat)
- **REST/GraphQL**: Typed methods, auth token management, pagination, rate limiting
- **Message Queue**: Producer/consumer, serialization, dead-letter, idempotent processing
- **File/Batch**: Watcher/poller, parser (CSV/JSON/XML), validator, chunked batch processor, quarantine
- **Webhook**: Signature verification, replay protection, delivery log, retry
- **Real-time**: Connection manager, heartbeat, reconnection, backpressure, buffering
- **Aptean Platform**: OAuth2 token manager via IAM, typed methods, webhook handler, health check

### 4. Generate Tests

Create `tests/integrations/<name>/` with conftest.py (fixtures), test_client.py, test_health.py, test_retry.py. Tests use mocks only (never real external systems), cover happy path + errors + retries + timeouts.

### 5. Generate Docker Compose Override

**Hostable types** (generate docker-compose.override.yaml): PostgreSQL, MySQL, MariaDB, SQL Server, Oracle, MongoDB, Redis, CosmosDB emulator, Cassandra, Elasticsearch, Kafka+Zookeeper, RabbitMQ, NATS, SFTP

**Non-hostable** (skip silently): Aptean Platform services, cloud queues, external APIs, cloud storage, cloud-managed DBs, Rocket U2, SQLite

Append service block to existing file (never overwrite). Env vars match .env.example names.

### 5.5. Populate .env.example

Create or append to `.env.example` with section header comment, all `${VAR}` from config.yaml with placeholder values and inline comments. Check for duplicates before appending.

### 6. Register Health Check

Wire into existing `/health` endpoint. If none exists, suggest `/polaris.healthcheck`.

### 7. Update Integration Inventory

Create/update `.polaris/integrations.yaml` with name, type, timestamp, config file paths. Append only, never modify existing entries. Non-blocking on failure.

### 8. Validation

1. Verify generated code compiles/imports
2. Run tests (all pass with mocks)
3. If Docker added: verify container starts
4. Verify config loads with placeholder env vars

### 9. Summary

List generated files, config details (resilience, health), next steps: copy .env.example to .env, review client code, run tests, docker compose up.

## Principles

- Config over code, secrets in env vars only, resilience by default, health checks mandatory
- Tests with mocks, non-destructive, one integration at a time, detect before generating
- SQL injection prevention (parameterized queries), pool config with comments, local dev ready (Docker Compose), .env.example always populated, inventory tracked

Context: $ARGUMENTS


**Telemetry**: Run: `polaris telemetry record integrate --feature <slug> --phase complete --agent claude`
