# 📆 Next Sprints Plan (Nov–Dec 2025)

This plan focuses on hardening Hermes end-to-end, finishing Federation P1.5→P2, and shipping a usable Developer Console. Each sprint targets shippable increments with clear acceptance criteria and quality gates.

---

## Sprint 2 (2 weeks): Runtime stability, observability, and DB hardening

Objectives
- Eliminate flaky startup/runtime issues across Windows, WSL2, and Linux.
- Production-grade observability: logs, metrics, traces, health, and profiling.
- Database correctness, migrations, and backup/restore confidence.

Scope & Deliverables
- App runtime
  - Windows start reliability: diagnose uvicorn exit code 1; add structured startup logs and fail-fast diagnostics.
  - Feature flags and config validation on boot (env contracts, helpful errors).
  - Graceful shutdown hooks; idempotent startup (safe if Redis/Postgres unavailable).
- Observability
  - OpenTelemetry tracing for FastAPI routes and DB calls (OTLP exporter env-gated).
  - Structured JSON logs (request_id, org_id, user_id, task_id), sampling for noisy subsystems.
  - Prometheus metrics: http server metrics, DB pool metrics, task orchestration counters.
  - Health endpoints: liveness/readiness with dependency breakdown (DB, Redis, background workers).
- Database
  - Alembic migration pass: capture current models → baseline migration; add CI check for drift.
  - Safe schema init: explicit create paths; guard rails for destructive ops.
  - Backups: `pg_dump` script + restore guide; verify on a fresh container.

Acceptance Criteria
- Startup on Windows and Linux prints a one-screen diagnostic summary and runs without manual tweaks.
- /api/v1/health shows detailed status (DB, Redis, queues), and readiness gates Kubernetes-friendly.
- Traces visible in local OTLP collector (optional), metrics scrapeable by Prometheus.
- Running `alembic upgrade head` on a new DB creates all required tables; `downgrade`/`upgrade` round trip passes.
- Backup/restore produces identical schema and minimal critical data restored (users, agents, orgs).

Quality Gates (must pass before sprint close)
- Build PASS; Lint/Typecheck PASS; Unit tests ≥ 85% coverage on services with new observability facets.

---

## Sprint 3 (2 weeks): Federation P2 and delivery guarantees

Objectives
- Make cross-org messaging reliable and auditable with retries, DLQs, and receipts.
- Secure federation by key rotation, policy cache, and stricter validation.

Scope & Deliverables
- Federation P2
  - Outbound retry policy with exponential backoff, jitter, and max-attempts per message.
  - Delivery receipts persisted; idempotency keys enforced across retries; dedup at inbox.
  - Dead-letter queue (DLQ) and admin UI to reprocess or discard.
  - HMAC key rotation protocol: rolling keys (K_n, K_{n+1}); require at least one valid.
  - Allowlist/denylist policy cache with TTL; metrics on decisions.
- Security & Compliance
  - Mandatory HMAC outside dev; structured federation audit log.
  - Clock skew tolerance; replay protection windows tightened.

Acceptance Criteria
- 3 failure scenarios (timeout, 5xx, HMAC mismatch) are retried correctly, deduped, and observable in UI/metrics.
- Admin can requeue or discard DLQ items; action produces audit events.
- Key rotation supported without downtime; new messages validated by K_{n+1}, old by K_n.

Quality Gates
- Integration tests simulate remote peer; chaos tests inject network faults; PASS.

---

## Sprint 4 (2 weeks): Developer Console MVP and multi-tenant RBAC

Objectives
- Ship a usable web console for org admins and developers.
- Introduce per-org isolation, roles, and quotas to prep for billing.

Scope & Deliverables
- Frontend (Next.js)
  - Auth flows polished (register/login/reset); robust client error handling.
  - Org admin pages: members, roles, API keys, federation contacts, inbox/DLQ views.
  - Agent marketplace browsing and semantic search; assign demo agents.
  - Live task/event timeline with WebSocket presence indicators.
- Backend
  - RBAC: roles {owner, admin, developer, member}. Route guards and tests.
  - API keys per org with scopes; rotation and last-used metadata.
  - Quotas: per-org rate limits and basic usage counters (backed by Redis).

Acceptance Criteria
- A new user can: register → create org → generate API key → register an agent → send a task → see live stream.
- Owners can manage roles and keys; developers can use keys but not change billing/roles.
- Quotas enforced; overage returns clear 429 with guidance.

Quality Gates
- E2E tests (Playwright) cover the happy path above; PASS in CI.

---

## Stretch Goals (pull into any sprint if capacity)
- Vector search uplift: re-indexing jobs, embedding versioning, nearest-neighbor quality dashboards.
- Background worker/queue abstraction for long jobs (RQ/Arq/Celery), with heartbeat and cancelation.
- File uploads + RAG pipeline for org knowledge bases.
- Client SDKs (Python/TypeScript) and example apps.

---

## Risks & Mitigations
- WSL2 networking flakiness for Postgres: prefer Docker-to-Docker for dev or SQLite for host runs; document `host.docker.internal` fallback.
- Redis outages: degrade gracefully (disable non-critical caches), keep task execution operational.
- Schema drift: enforce migration checks in CI; block merges on drift.

---

## Tracking & Metrics
- SLOs: p95 API latency, task success rate, message delivery latency, DLQ rate.
- Dashboards: health, errors by route, federation retries, top org usage.

---

## Immediate Next Steps
- Create issues for Sprint 2 stories with Acceptance Criteria and owners.
- Wire OpenTelemetry and Prometheus in dev; add flags to disable in minimal envs.
- Add Windows startup diagnostics and capture logs to file for the uvicorn exit-1 bug.
