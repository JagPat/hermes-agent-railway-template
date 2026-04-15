# Skill — Chanakya Portfolio Coordination

**Namespace:** `chanakya`
**Intended callers:** `chanakya:brain` — specifically when
`PortfolioOrchestrator` is coordinating a multi-trade execution plan.

## When to use

When multiple verdicts generate trade candidates that share a
portfolio budget, a sector exposure cap, or a cash pool — and those
candidates must be reconciled into a single coherent execution plan.

## Inputs

- Current portfolio snapshot (holdings, cash, sector exposure).
- Trade candidates (symbol, direction, target size, confidence).
- Sector exposure limits and portfolio-level constraints.
- Rebalance targets (if any, from `analytics/rebalancing.js`).
- OTS: broker readiness, execution eligibility, capital allocation.

## Process

1. **Verify OTS** — if `broker_readiness` or `execution_eligibility`
   returns false, abort the plan and return a single `paused` plan
   with the reason.
2. **Rank candidates** by confidence × regime fit × fundamentals
   weight, using the Brain's existing scoring; do not invent a new
   ranking function.
3. **Apply hard limits** in this order:
   - Kill switch / drawdown (risk manager).
   - Sector exposure cap.
   - Position concentration cap.
   - Free cash available (from snapshot, reconciled with OTS
     capital allocation).
4. **Resolve conflicts**:
   - If two candidates need the same cash, prefer the higher-ranked
     one.
   - If a BUY and a SELL exist for the same symbol, net them into a
     single adjustment.
   - If a rebalance target disagrees with a candidate verdict, the
     rebalance target wins unless the candidate explicitly overrides
     it via an annotation.
5. **Emit an execution plan** — ordered, with explicit sizing and
   per-trade rationale. Mark any trade that pushes a limit to its
   edge.

## Output format

```json
{
  "status": "ready | paused | partial",
  "pause_reason": "...",
  "plan": [
    {
      "symbol": "...",
      "action": "BUY | SELL | ADJUST",
      "qty": 0,
      "notional_inr": 0,
      "rationale": "...",
      "source_verdict_ids": ["..."],
      "limits_touched": ["sector_cap", "concentration", "cash"]
    }
  ],
  "unplaced_candidates": [
    { "symbol": "...", "reason": "..." }
  ],
  "constraints_respected": {
    "broker_readiness": true,
    "execution_eligibility": true,
    "sector_cap": true,
    "concentration": true,
    "cash_available": true
  }
}
```

## Rules

- Never emit a plan that violates a hard limit — if you cannot fit
  a candidate within limits, list it in `unplaced_candidates` with a
  reason.
- Never exceed the rollout cohort's execution scope in pilot mode.
- Do not place orders directly — this skill builds the plan;
  AutoPilot + the broker interface execute it.
- If the snapshot and OTS disagree on cash, OTS wins.
