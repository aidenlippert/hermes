# Technical Sprints (5–8) — From Vision to Code

This document breaks down the next phases into concrete code work: schemas, endpoints, services, UI, tests, and acceptance criteria. It assumes the current state: FastAPI backend, async SQLAlchemy, SQLite/Postgres, Redis, A2A substrate, Federation P1, and Next.js frontend.

---

## Sprint 5: Multi‑Agent Workflows (DAG orchestration)

Goal
- Support authoring and running multi‑step workflows with dependencies, parallelism, retries, and live streaming.

Core Concepts
- Workflow: an immutable DAG template (versioned)
- WorkflowRun: an execution instance of a Workflow
- Node: step definition (agent call, tool, human gate)
- NodeRun: runtime state for a node with inputs/outputs/events

Backend
- Schema (alembic migration):
  - workflows(id, org_id, name, version, spec_json, created_at)
  - workflow_runs(id, workflow_id, org_id, status, started_at, finished_at, input_json, metadata)
  - workflow_nodes(id, workflow_id, key, type, config_json)
  - workflow_edges(id, workflow_id, from_key, to_key, condition_json)
  - node_runs(id, workflow_run_id, node_key, status, attempt, input_json, output_json, started_at, finished_at, error_json)
- Services:
  - services/workflows.py: compile/validate DAG, topological sort, parameter binding
  - services/workflow_runner.py: orchestrator loop, parallel fan‑out, retries, backoff, cancellation
  - services/artifacts.py: store/retrieve large outputs; integrate Redis streams for event fanout
- APIs (FastAPI):
  - POST /api/v1/workflows (create/update version)
  - GET /api/v1/workflows/:id (fetch)
  - POST /api/v1/workflows/:id/run (start run)
  - GET /api/v1/workflow_runs/:id (status + nodes)
  - WS /api/v1/ws/workflow_runs/:id (live node events)
- Execution integration:
  - Node type "agent_call": invoke existing A2A execution path
  - Node type "tool_call": plug local tools (HTTP, Python function)
  - Node type "human_gate": pause until approve/deny via API/UI

Frontend (Next.js)
- Visual builder (React Flow or lightweight custom):
  - pages: /workflows, /workflows/[id]
  - components: WorkflowCanvas, NodePalette, EdgeEditor, RunPanel
- Run view with live timeline and per‑node logs/results

Tests
- Unit: DAG validation (cycles, missing nodes, invalid edges), parameter binding
- Integration: run a 3‑node workflow (parallel branch + join) and assert outputs and statuses
- E2E: create workflow → run → watch WS events → success

Acceptance Criteria
- Create a workflow with 3+ nodes and a conditional branch, start a run, and see parallel execution with correct join.
- Node retries (configurable) work with exponential backoff; cancellation stops outstanding nodes.
- Live WS shows transitions: queued → running → completed/failed, with logs and outputs.

---

## Sprint 6: Agent Economy (pricing, wallets, escrow)

Goal
- Introduce basic economic primitives to price, pay, and settle for agent work.

Phased Approach
- Phase A (simulated credits): org wallets with credits; debits/credits in DB; no external payment yet.
- Phase B (payment adapters): pluggable gateway (Stripe test mode) and per‑org billing config.
- Phase C (escrow): hold funds on award; settle on delivery/validation; refunds on failure.

Backend
- Schema:
  - wallets(id, org_id, balance_cents, currency, updated_at)
  - ledger(id, wallet_id, type[debit|credit|hold|release], amount_cents, ref_type, ref_id, metadata, created_at)
  - prices(agent_id, model, unit, amount_cents, currency, effective_at)
  - contracts add columns: price_model, max_spend_cents, escrow_ledger_id
- Services:
  - services/wallets.py: get/adjust balance, create holds, releases, refunds
  - services/pricing.py: resolve price for agent action (subscription|per-use|auction reserve)
  - services/settlement.py: on delivery/validation, settle escrow and write ledger entries
  - services/payments.py: adapter interface; stripe_test.py (Phase B)
- APIs:
  - GET/POST /api/v1/orgs/:id/wallet (view/top‑up in dev via credits)
  - GET/POST /api/v1/agents/:id/pricing
  - Webhooks (Phase B): /api/v1/payments/webhook

Frontend
- Wallet view: balance, history, test top‑ups (dev only)
- Pricing editor per agent; show estimated cost in workflow/contract UI
- Delivery summary with settlement status

Tests
- Unit: ledger invariants (sum of holds + debits ≤ credits), double‑spend guards
- Integration: award contract → create escrow hold → deliver → settle → ledger state correct
- Adapter tests (Phase B): Stripe test mode lifecycle

Acceptance Criteria
- In dev mode, org can top‑up credits, run workflows that debit balances, and see ledger history.
- Escrow is created on award and released on successful delivery; failures refund holds.

---

## Sprint 7: Meta‑Intelligence (agent factory + sandbox)

Goal
- Enable “agents that create agents” safely with a scaffold pipeline, evaluation harness, and sandboxed execution.

Components
- Agent Templates: descriptors for capabilities, prompts, tools, policies
- Factory Pipeline: generate code from template + LLM; assemble config; write repo/module
- Sandbox Runner: execute agent code in isolated process/container
- Evaluation Harness: run test suites against new agent; score on accuracy/latency/cost
- Registry & Versioning: store agent versions, provenance, and approval state

Backend
- Schema:
  - agent_templates(id, name, descriptor_json, created_at)
  - agent_versions(id, agent_id, version, repo_ref, manifest_json, created_at, approved)
  - agent_builds(id, template_id, status, logs, artifacts_ref, created_at)
  - agent_evals(id, agent_version_id, suite, score_json, passed, created_at)
- Services:
  - services/agent_factory.py: scaffold/generate code from template
  - services/sandbox.py: run agents with resource limits (subprocess policy; container optional)
  - services/agent_eval.py: run eval suites; compute scores; gate approvals
- APIs:
  - POST /api/v1/agent_factory/build (from template params)
  - GET /api/v1/agent_builds/:id
  - POST /api/v1/agents/:id/versions/:v/approve

Frontend
- Agent factory UI: choose template → parameters → build → watch logs → run evals → approve/publish
- Eval results and version history

Tests
- Unit: template rendering, sandbox policy, scoring functions
- Integration: build a simple WebSearcher agent, pass minimal eval suite, approve and publish

Acceptance Criteria
- From the console, a user can generate a new agent from a template, run evals, and publish a version that becomes discoverable.
- Sandbox enforces timeouts and memory limits; failures are reported with logs.

---

## Sprint 8: Global Scale (registry, hubs, governance)

Goal
- Prepare for global distribution: resilient discovery, regional hubs, and governance foundations.

Components
- Distributed Registry (phased):
  - Phase A: signed snapshots of registry (DAG of manifests) distributed over HTTP/IPFS
  - Phase B: optional blockchain anchoring for tamper‑evident checkpoints
- Regional Federation Hubs: caching relays that reduce cross‑region latency; policy mirrors
- Governance:
  - Org registration/verification workflows; attestations
  - Policy bundles; deny/allow distribution lists

Backend
- Schema:
  - registry_snapshots(id, root_hash, manifest_url, created_at, signature)
  - attestations(id, subject, type, payload_json, issuer, signature, created_at)
- Services:
  - services/registry_sync.py: export/import signed manifests; IPFS adapter optional
  - services/hub_proxy.py: regional relay for federation with caching and rate limits
  - services/governance.py: manage attestations and verification flows
- APIs:
  - GET /api/v1/registry/snapshot (export); POST /api/v1/registry/import (import)
  - Admin: POST /api/v1/attestations

Infra
- Queues/workers for heavy jobs; horizontal scale plan; rate limit tiers per org/region

Tests
- Integration: snapshot export/import round‑trip; hub proxy cache correctness under churn
- Security: signature verification, tamper detection on manifests

Acceptance Criteria
- Nodes can export a signed registry snapshot and another node can import/verify it.
- A hub proxy can relay cross‑region federation traffic with measurable latency reduction.

---

## Cross‑cutting Work

- Observability: traces/metrics/logs for new services; dashboards and SLOs
- Security: key rotation for federation; DID/ed25519 signatures as upgrade path
- Migrations: every sprint ships Alembic scripts + CI drift checks
- Docs: API reference and runbooks; threat models for new attack surfaces

---

## Suggested Sequence & Guardrails

- Keep sprints shippable: each ends with a demoable feature available in the UI and API.
- Prefer feature flags for Phase B/C items (payments, distributed registry) to keep mainline stable.
- Write happy‑path tests first, then inject faults (timeouts, 5xx, retries) to harden.

---

## Kickoff Checklist (Sprint 5)

- Create Alembic migrations for workflow tables
- Scaffold services/workflows.py and services/workflow_runner.py
- Add API routers under backend/api/v1/workflows.py
- Add WS endpoint and events (node transitions)
- Frontend: create /workflows route and initial canvas with mock nodes
- Tests: unit DAG validation; integration run with parallel branch + join
