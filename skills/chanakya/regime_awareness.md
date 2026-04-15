# Skill — Chanakya Market Regime Awareness

**Namespace:** `chanakya`
**Intended callers:** `chanakya:brain`, `chanakya:worker`,
`chanakya:analyst`.

## When to use

When the Brain or the analysis worker needs to reason about the
current market regime — what it is, whether it just changed, and how
strategies have historically performed in comparable regimes.

## Process

1. **Classify the current regime** using Research inputs:
   - Trend direction (bull / bear / sideways).
   - Volatility bucket (low / normal / elevated / crisis).
   - Breadth (advance-decline, % above 200DMA).
   - Macro overlay if available.
2. **Check for a transition** against the last regime recorded in
   memory for this namespace. If the regime has flipped, emit a
   `regime_transition` event and record the new regime.
3. **Look up historical strategy performance** for this regime
   class from `HermesMemoryStore`:
   - Which strategy families produced uplift?
   - Which failed?
   - Any concept-drift flags attached to them?
4. **Recommend regime-appropriate actions**:
   - Which strategies to enable / disable.
   - Position-sizing posture (aggressive / neutral / defensive).
   - Rebalance priority (urgent / normal / defer).
5. **Never mutate live state** — this skill produces recommendations
   that flow through AutoPilot and the risk manager; it does not
   place orders itself.

## Output format

```json
{
  "current_regime": {
    "trend": "bull | bear | sideways",
    "volatility": "low | normal | elevated | crisis",
    "breadth": "...",
    "macro_overlay": "..."
  },
  "transition_from_prior": true | false,
  "prior_regime": "...",
  "strategies_recommended_on": ["..."],
  "strategies_recommended_off": ["..."],
  "sizing_posture": "aggressive | neutral | defensive",
  "rebalance_priority": "urgent | normal | defer",
  "evidence": [
    { "claim": "...", "source": "research | memory | ots" }
  ]
}
```

## Rules

- Regime classification must be defensible — cite the indicators
  that drove it.
- Never skip the transition check; a missed transition is the most
  damaging error this skill can make.
- When recommending strategies ON, respect the active rollout mode
  (`ADVISORY_ONLY`, `CONTROLLED_EXECUTION_PILOT`).
- Do not invent macro data — if the prompt lacks a macro overlay,
  say so and continue without it.
