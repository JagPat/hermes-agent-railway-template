# Chanakya-Bot — Product Overview

This Hermes instance is dedicated to **Chanakya-Bot** — Jagrut Patel's
personal AI hedge fund manager for the Indian stock market.

## What Chanakya-Bot is

A full-stack autonomous trading system:

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
- `hermes.vitan.in` — This AI gateway.

## Sessions

Each Chanakya service gets its own session for persistent context:
- `chanakya:brain` — Main AI orchestration (verdicts, recommendations).
- `chanakya:worker` — Background analysis loop.
- `chanakya:central` — OTS queries.
- `chanakya:sage` — User-facing chat.
- `chanakya:optimizer` — Strategy optimisation (heavy, dedicated context).
- `chanakya:analyst` — Deep analysis (heavy, dedicated context).

## What to remember across sessions

- Current strategy states and mutation history.
- Past verdict accuracy and concept-drift signals.
- Market regime transitions and which strategies performed in each
  regime.
- Rollout mode (`ADVISORY_ONLY`, `CONTROLLED_EXECUTION_PILOT`, …) and
  pilot-cohort gating decisions.
- Broker readiness / token lifecycle state summaries.

## What NOT to do

- Invent tickers, holdings, or broker responses that aren't in the
  verified truth sources.
- Treat past learned insights as current truth — always reconcile
  with the Operational Truth Service (OTS) before acting.
- Leak principals, keys, or raw broker tokens into prompts.
