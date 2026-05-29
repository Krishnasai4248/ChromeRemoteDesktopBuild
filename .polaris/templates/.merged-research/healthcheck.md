---
description: Add standardized health endpoints to a service following organization best practices.
---

## User Input

**Telemetry**: Run: `polaris telemetry record healthcheck --feature <slug> --phase start --agent {{AGENT_NAME}}`


```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Add four standardized health endpoints to a service: `/health`, `/liveness`, `/readiness`, and `/detailed`. Supports multiple languages and frameworks with correlation ID tracking and component checks.

## Execution Steps

### 1. Detect Language and Framework

Scan the project to identify:

- **Python**: FastAPI, Django, Flask
- **Node.js**: Express, NestJS, Fastify
- **Go**: net/http, gin, echo
- **C#**: ASP.NET Core, .NET Minimal API
- **Java**: Spring Boot, Quarkus

If multiple frameworks are detected, ask the user which one to target.

### 2. Identify Components

Detect service dependencies that need health checks:

- **Database**: PostgreSQL, MySQL, SQLite, MongoDB, Redis
- **Message queue**: RabbitMQ, Kafka, SQS
- **Cache**: Redis, Memcached
- **External APIs**: Any outbound HTTP calls
- **File system**: Required writable paths

Ask the user to confirm the detected components.

### 3. Generate Health Endpoints

Create four endpoints following the organization standard:

#### `/health` (Basic)
- Returns `200 OK` with `{"status": "healthy"}`
- No authentication required
- Used by load balancers and basic monitoring

#### `/liveness` (Kubernetes)
- Returns `200 OK` if the process is running
- Minimal checks - just confirms the app can respond
- Used by Kubernetes liveness probe

#### `/readiness` (Kubernetes)
- Returns `200 OK` only if the service can handle requests
- Checks database connectivity, required services availability
- Returns `503 Service Unavailable` if not ready
- Used by Kubernetes readiness probe

#### `/detailed` (Operations)
- Returns comprehensive health information:

```json
{
  "status": "healthy",
  "version": "2026.02.0",
  "uptime_seconds": 3600,
  "correlation_id": "abc-123",
  "checks": {
    "database": {"status": "healthy", "latency_ms": 12},
    "redis": {"status": "healthy", "latency_ms": 3},
    "disk": {"status": "healthy", "free_gb": 45.2}
  }
}
```

### 4. Add Correlation ID Support

Add middleware/interceptor that:

1. Reads `X-Correlation-ID` header from incoming requests
2. Generates a UUID if not present
3. Passes it through to all downstream calls
4. Includes it in health check responses
5. Logs it with every log entry

### 5. Add Version Injection

Read version from:
1. `VERSION` file (CalVer, preferred)
2. `package.json` version field
3. `pyproject.toml` version field
4. Environment variable `APP_VERSION`

Include version in `/health` and `/detailed` responses.

### 6. Generate Tests

Create tests for each endpoint:

```
tests/
  test_health.py (or test_health.ts, health_test.go, etc.)
    - test_health_returns_200
    - test_liveness_returns_200
    - test_readiness_healthy_when_deps_available
    - test_readiness_503_when_deps_unavailable
    - test_detailed_includes_all_components
    - test_correlation_id_passthrough
    - test_version_included
```

### 7. Update Docker Health Check

If a Dockerfile exists, add or update the HEALTHCHECK instruction:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
```

### 8. Summary

```
Health Endpoints Added!

  /health     - Basic health check (200 OK)
  /liveness   - Kubernetes liveness probe
  /readiness  - Kubernetes readiness probe (checks: db, redis)
  /detailed   - Full operational health with version and timing

  Framework:  <detected-framework>
  Components: <db>, <cache>, ...
  Tests:      <test-count> test cases added

Next steps:
  1. Review generated health check code
  2. Run tests: <detected test command>
  3. Update Kubernetes manifests with probe configuration
```

## Operating Principles

- **Detect, don't assume**: Always identify the framework before generating code
- **Framework-idiomatic**: Use native patterns (FastAPI routers, Express middleware, Spring actuator, etc.)
- **Test everything**: Generate tests for all health check scenarios
- **No secrets in responses**: Health endpoints must never expose credentials or internal details
- **Fail open for liveness**: Liveness should almost always return 200 (only fail if process is truly stuck)

## Context

{ARGS}


**Telemetry**: Run: `polaris telemetry record healthcheck --feature <slug> --phase complete --agent {{AGENT_NAME}}`
