# Chanakya-Bot — Product Overview

**Namespace:** `chanakya`
**Audience:** Sessions prefixed `chanakya:` (Web, Worker, Central, Bot,
Sage, feature-specific sessions).

## What Chanakya-Bot is

Chanakya-Bot is Jagrut Patel's personal AI hedge fund manager for the
Indian stock market. It is a full-stack autonomous trading system:

- Analyses stocks, generates buy/sell/hold verdicts.
- Manages portfolios and executes trades through broker APIs
  (Zerodha, Dhan).
- Continuously self-learns from outcomes.
- Ships as a Next.js + Node.js monorepo (`JagPat/chanakya-bot`).

## Deployment surface (on Coolify)

- `app.vitan.in` — Chanakya web frontend (Next.js).
- `worker.vitan.in` — Background worker (analysis, scheduling,
  monitoring).
- `central.vitan.in` — Central service (OTS, lineage, policy engine;
  Phase 6A/B in progress).
- `hermes.vitan.in` — Central AI gateway (this service).

## Critical isolation rule

Chanakya is **not** Vitan Architects. The `chanakya:` namespace must
never reference the Vitan business, Paperclip agents, architecture
projects, or any `vitan:*` session content. Trading intelligence and
architecture consultancy are kept in separate memory spaces inside the
same Hermes deployment.

## What the namespace should remember across sessions

- Current strategy states and mutation history.
- Past verdict accuracy and concept-drift signals.
- Market regime transitions and which strategies performed in each
  regime.
- Rollout mode (`ADVISORY_ONLY`, `CONTROLLED_EXECUTION_PILOT`, …) and
  pilot-cohort gating decisions.
- Broker readiness / token lifecycle state summaries.

## What the namespace must NOT do

- Invent tickers, holdings, or broker responses that aren't in the
  verified truth sources listed below.
- Treat past learned insights as current truth — always reconcile
  with the Operational Truth Service (OTS) before acting.
- Leak principals, keys, or raw broker tokens into prompts.
