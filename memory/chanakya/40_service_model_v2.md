# Chanakya — Service Model V2 (Central / OTS Cutover)

Reference docs in `JagPat/chanakya-bot`:

- `docs/architecture/CHANAKYA_SERVICE_MODEL_V2.md`
- `docs/architecture/CHANAKYA_CENTRAL_CUTOVER_PLAN.md`
- `docs/architecture/OTS_API_CONTRACT.md`
- `packages/core/truth/index.js`

## Why Central exists

Chanakya V2 introduces a new service — **`chanakya-central`**
(deployed at `central.vitan.in`) — as the canonical **Operational
Truth Service (OTS)**. Historically the web frontend and worker each
computed their own view of system state; that led to inconsistent
UIs, divergent decisions, and brittle failure modes.

Central's job is to **resolve** canonical state in one place. Every
other surface (web, worker, bot) trusts Central.

## What the OTS resolves

1. **Active strategy state** — which strategies are currently in
   force, what mode they run in, last mutation.
2. **Broker readiness** — can the system actually place orders right
   now? Tokens valid? Circuit breakers open?
3. **Capital allocation** — how much free cash, how much is reserved
   for in-flight orders, sector exposure.
4. **Execution eligibility** — rollout mode, pilot gating, market
   hours, kill switch.
5. **System health** — provider availability, AI gateway status,
   data freshness, recent error rates.

## Cutover phases

- **Phase 6A — Dark deploy**: `chanakya-central` runs alongside
  existing worker/web; no traffic is routed to it, but it mirrors the
  calculations and is observed.
- **Phase 6B — Traffic switch**: Web and bot start consuming Central
  for the five truth endpoints above. Worker continues to also
  compute state so both sources can be reconciled.
- **Phase 6C — Worker route removal**: Once Central is trusted, the
  worker stops computing these states; worker only *reports* state,
  Central *resolves* it.

## How Hermes should reason about Central

- Treat Central as the live source of truth — never overrule it.
- If an insight stored in `HermesMemoryStore` contradicts what
  Central reports right now, Central wins. The insight is historical
  context, not current truth.
- When a skill needs broker readiness, capital, strategy state, or
  execution eligibility, it should mention which OTS endpoint it is
  reasoning about so downstream callers can verify.
- Never cache OTS responses in Hermes memory — they are operational,
  not learning signals.

## Frontend responsibility (render-only)

`apps/web` becomes render-only against Central: it should fetch truth
from OTS endpoints and display them. It should not recompute strategy
state, cash, or readiness locally.
