# Skill — Chanakya Strategy Evolution

**Namespace:** `chanakya`
**Intended callers:** `chanakya:optimizer`, `chanakya:brain`.

## When to use

When the Brain is considering mutating a strategy (via
`packages/core/brain/strategy/closedLoopOptimizer.js` or
`strategy/optimizer.js`) and wants to ground the mutation in both
backtest evidence AND the history of what has worked in this system.

## Process

1. **Pull mutation history** — query `EvolutionLog` for prior
   mutations of this strategy family. If none, say so; do not guess.
2. **Cluster prior mutations** by effect:
   - Uplift > baseline on walk-forward validation.
   - Neutral / marginal.
   - Regression.
3. **Pull `HermesMemoryStore` insights** that mention the same
   strategy, regime, or parameter family.
4. **Propose mutations** that are grounded in the clusters above:
   - Favour mutations that historically produced uplift in a
     comparable regime.
   - Avoid repeating mutations that regressed.
   - If the closed-loop optimizer's walk-forward gate has already
     been computed, respect it — don't propose mutations that would
     fail that gate.
5. **Specify the walk-forward test** each proposal must pass before
   it is promoted (time window, uplift threshold, confidence).
6. **Rank** proposals by expected uplift * confidence * novelty.

## Output format

```json
{
  "strategy_id": "...",
  "regime": "...",
  "history_summary": {
    "n_prior_mutations": 0,
    "n_uplift": 0,
    "n_neutral": 0,
    "n_regression": 0
  },
  "proposals": [
    {
      "mutation": "...",
      "rationale": "...",
      "supporting_insights": ["insight_id", "..."],
      "expected_uplift": 0.0,
      "confidence": 0.0,
      "walk_forward_test": { "window": "...", "uplift_threshold": 0.0 }
    }
  ],
  "do_not_retry": ["...past mutations that regressed..."]
}
```

## Rules

- Only propose mutations that can be validated by the closed-loop
  optimizer; speculative hand-wavy tweaks are out of scope.
- Never propose changes that bypass the risk manager or raise
  exposure beyond the current pilot cohort's limits.
- Insights pulled from memory must cite the underlying
  `AIDecisionLog` entries they are derived from, when available.
- Do not produce proposals while in `ADVISORY_ONLY` mode unless the
  caller explicitly asks for "advisory-only mutations".
