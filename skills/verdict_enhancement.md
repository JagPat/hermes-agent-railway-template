# Skill — Chanakya Verdict Enhancement

**Namespace:** `chanakya`
**Intended callers:** `chanakya:brain`.

## When to use

When the Brain is generating a buy / sell / hold verdict and has
already built a prompt via `HermesContextBuilder`. This skill
augments — does not replace — the existing self-learning pipeline.

## Inputs expected in the prompt

- **Symbol + regime** — e.g. `RELIANCE` under `bull_volatile`.
- **Research snapshot** — fundamentals, technicals, news, valuation.
- **Portfolio context** — current position, cost basis, holding
  period.
- **HermesContext block** — prior decision history + validated
  insights injected by `HermesContextBuilder`.
- **Confidence stats** — recent accuracy and
  `HermesFeedback.getConfidenceCalibration()` output.

## Process

1. **Anchor on prior decisions** — if Hermes has an unresolved prior
   verdict for this symbol (in `AIDecisionLog`), reconcile it
   explicitly. State whether the new verdict confirms, reverses, or
   refines the prior one.
2. **Respect concept drift signals** — if recent accuracy has
   dropped below baseline (flagged by `HermesFeedback`), lower the
   confidence on the new verdict and say so in the rationale.
3. **Reason across three horizons** — short (<1w), medium (1-4w),
   long (>4w). Give an explicit verdict for each horizon, not a
   single collapsed one.
4. **Cite evidence** — every claim in the rationale must point to an
   item in the prompt: a research figure, an insight, a technical
   signal, or a prior decision id.
5. **Name the regime** the verdict depends on and the invalidation
   condition that would flip it.
6. **Never invent numbers** — if a ratio or fundamental is missing,
   say "not in research" and continue without fabricating.

## Output format (strict)

```json
{
  "verdict": "BUY" | "SELL" | "HOLD",
  "by_horizon": {
    "short": "BUY" | "SELL" | "HOLD",
    "medium": "BUY" | "SELL" | "HOLD",
    "long": "BUY" | "SELL" | "HOLD"
  },
  "confidence": 0.0,
  "confidence_notes": "...",
  "regime_assumption": "...",
  "invalidation": "...",
  "rationale": [
    { "claim": "...", "evidence_ref": "..." }
  ],
  "prior_decision_reconciliation": "confirms | reverses | refines | none",
  "drift_flag": true | false
}
```

## Rules

- Never bypass the Brain's existing schema — emit JSON that the
  Brain can parse.
- Never pull from `vitan:*` sessions or memory.
- Never output a verdict more confident than the calibration data
  justifies.
- Do not treat `HermesMemoryStore` insights as current truth — they
  are historical context.
- Execution decisions belong to `AutoPilot` — this skill produces
  verdicts, not orders.
