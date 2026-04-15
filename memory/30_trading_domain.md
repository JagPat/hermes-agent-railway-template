# Chanakya — Trading Domain Facts

## Indian market basics

- **Exchanges**: NSE and BSE.
- **Market hours (IST)**: 09:15 – 15:30, Monday through Friday,
  excluding NSE/BSE holidays.
- **Currency**: INR.
- **Regulation**: SEBI.
- Session management is enforced by `packages/core/market/hours.js`;
  live trading is gated by market hours.

## Broker adapters

- **Zerodha** (primary live adapter).
  - TokenBot (`apps/tokenbot/*`) is the refresh authority.
  - Zerodha does NOT issue long-lived refresh tokens; tokens expire
    daily at ~07:30 IST.
  - Refresh flow is headless browser automation (Puppeteer) using the
    user's `kite_user_id`, `password`, and `totp_secret`. The UI
    collects and encrypts these credentials.
  - Refresh contract is connection-scoped: callers send
    `brokerConnectionId`, no silent fallback to a service-level token.
- **Dhan** — supported, uses OAuth-style redirect (unlike Zerodha).
- **Mock broker** — used by Brain-driven backtests
  (`packages/core/brain/backtest/index.js`).

## The 3 universal sources of truth

Chanakya's self-learning loop and all verdicts must ground themselves
in these three sources — never in memory alone:

1. **Portfolio snapshot** — holdings, cash, positions, owned by the
   snapshot service.
2. **AIDecisionLog** — every verdict emitted by the Brain, its
   rationale, and its eventual outcome.
3. **Market data** — prices, fundamentals, news, owned by Research.

## Risk controls

- `packages/core/risk/index.js` — kill switch, drawdown exposure,
  data freshness checks.
- `packages/core/brain/systemState.js` — global trading state,
  kill switch, auto-trading.
- `packages/core/brain/agents/riskLimit.js` — dynamic risk limits.
- `packages/core/utils/circuitBreaker.js` + `rateLimiter.js` —
  resilience gates on provider/broker calls.

## Rollout modes

- `ADVISORY_ONLY` — Brain emits verdicts but does not place orders.
- `CONTROLLED_EXECUTION_PILOT` — execution enabled for the pilot
  cohort only, under pilot gates.
- Any move beyond pilot requires an explicit promotion gate decision,
  not an automatic escalation from `HermesContextBuilder`.

## Strategy optimisation / closed loop

- `packages/core/brain/strategy/optimizer.js` — AI parameter
  suggestions from backtests.
- `packages/core/brain/strategy/closedLoopOptimizer.js` — walk-forward
  validation and uplift gates.
- `packages/core/brain/learning/*` — logs learning signals from
  backtest/simulation.
- `packages/core/brain/rebalancer/optimizer.js` — self-correcting
  optimization for rebalance strategies.

## Do-not-fabricate list

Hermes must never invent the following for Chanakya:
- Tickers, ISINs, or sector classifications not present in Research
  outputs.
- Portfolio holdings or cash balances — always fetch from snapshot.
- Broker/account identifiers.
- Token expiry or refresh timestamps — query TokenBot.
- Historical accuracy numbers — compute from `AIDecisionLog` and
  `HermesMemoryStore`, never guess.
