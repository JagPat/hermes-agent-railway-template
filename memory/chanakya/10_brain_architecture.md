# Chanakya — Brain-Centric Modular Architecture

Source: `docs/architecture/ADR-001-modular-architecture.md` and
`docs/architecture/SYSTEM_MAP.md` in `JagPat/chanakya-bot`.

## Three-module core

The monorepo `packages/core` is split into three logical modules with
strict boundaries:

1. **Brain** — central intelligence, orchestration, business logic,
   AI agents. Defined by `packages/core/brain/interface.js`.
2. **Research** — market data, fundamentals, news. Defined by
   `packages/core/research/interface.js`.
3. **Broker** — execution, orders, portfolio/account data, token
   lifecycle. Defined by `packages/core/broker/interface.js`.

## The two hard rules (ADR-001)

1. **External Access Rule (the "Moat")**
   - `apps/web` (Next.js UI) and `apps/bot` (Telegram) are external
     clients. They MUST NOT import internal classes from
     `packages/core/brain|research|broker`.
   - Web talks to the Brain via `/api/brain/...` HTTP endpoints.
   - Bot talks to the Brain via the public `BrainInterface`.

2. **Internal Dependency Rule (the "Core")**
   - Brain depends on Research and Broker only through their
     interfaces.
   - Research and Broker never depend on the Brain.
   - Direct imports of `ResearchService.js`, `ZerodhaBroker.js`, etc.
     from Brain business logic are forbidden.

## Key entrypoints (from SYSTEM_MAP.md)

- `apps/web/app/page.tsx`, `apps/web/app/layout.tsx` — UI shell.
- `apps/web/app/api/**/route.ts` — HTTP API surface.
- `apps/web/app/actions.ts` — server actions (backtests, rebalancing).
- `apps/bot/index.js` — Telegram bot + scheduled routines.
- `packages/core/index.js` — core service endpoints.
- `packages/core/execution/scheduler.js` — market-hours cron,
  triggers `AnalysisWorker.runAnalysis()` every 15 minutes during
  market hours.
- `apps/tokenbot/server.js` — broker auth / token refresh service.

## Autobot & orchestration

- `packages/core/brain/worker.js` is the analysis loop — batches
  holdings/watchlist, produces recommendations, hands execution to
  AutoPilot and the PortfolioOrchestrator.
- `packages/core/brain/agents/autopilot.js` is the live execution
  gate (kill switch, promotion gates, dynamic limits).
- `packages/core/brain/agents/portfolioOrchestrator.js` coordinates
  multi-trade execution plans across a portfolio.

## Failure handling

- **Research failure** → Brain must degrade gracefully ("Analysis
  Unavailable" / "Technical Data Only"), not crash.
- **Broker failure** → Brain reports "Execution Failed" or "Data
  Stale", without exposing stack traces.

## Chanakya identity

- Identity cookie: `chanakya_user_id` (HttpOnly, Secure, SameSite=lax).
- Bootstrap route: `/start` sets the cookie and redirects to
  `/settings?tab=brokers`.
- Auth helpers: `apps/web/lib/auth-helper.ts`,
  `apps/web/lib/auth-server.ts`.

## Broker identity

- Canonical execution linkage: `Portfolio.executionBrokerConnectionId`.
- Legacy linkage `Portfolio.brokerConnectionId` still exists for
  compatibility but is being retired.
- `packages/core/broker/sessionManager.js`'s `withSession()` no
  longer defaults `connectionId` to `SERVICE_BROKER_CONNECTION_ID`.
