# Skill — Chanakya Self-Learning Synthesis

**Namespace:** `chanakya`
**Intended callers:** `chanakya:brain`, `chanakya:analyst`.

## When to use

Periodically (daily or weekly) to distill validated insights from
`HermesMemoryStore` into higher-level trading rules, prune stale or
contradictory insights, and maintain a healthy knowledge hierarchy.

## Process

1. **Read the insights window** — last N days of `HermesMemoryStore`
   entries, tagged with source `AIDecisionLog` ids, symbols, and
   regimes.
2. **Group insights** by:
   - Symbol family.
   - Regime.
   - Strategy / feature of origin
     (`STRATEGY_OPTIMIZATION`, `DEEP_ANALYSIS`, …).
3. **Detect contradictions** — two insights for the same
   symbol + regime that recommend opposite actions. Flag them.
4. **Score each insight** on:
   - Sample size (how many outcomes support it).
   - Recency.
   - Source confidence (from `HermesFeedback`).
5. **Promote** strong, consistent insights into higher-level rules:
   - Candidate rules must be framed as `if <condition> then
     <expectation>` in one sentence.
   - Each rule must cite at least 3 underlying insights.
6. **Prune**:
   - Insights with score below threshold and no recent
     reinforcement.
   - Insights contradicted by more recent, higher-quality evidence.
   - Duplicates (keep the one with the larger sample).
7. **Never delete** insights that are the sole source of a
   contradiction — keep them and flag the contradiction for human
   review.

## Output format

```json
{
  "window_days": 0,
  "insight_count_before": 0,
  "insight_count_after": 0,
  "promoted_rules": [
    {
      "rule": "if <cond> then <expect>",
      "regime": "...",
      "supporting_insight_ids": ["..."],
      "sample_size": 0,
      "confidence": 0.0
    }
  ],
  "pruned": [
    { "insight_id": "...", "reason": "..." }
  ],
  "contradictions": [
    {
      "symbol_or_family": "...",
      "regime": "...",
      "insight_ids": ["...", "..."],
      "needs_human_review": true
    }
  ],
  "drift_flags": [
    { "family": "...", "observation": "..." }
  ]
}
```

## Rules

- Never promote a rule from a single insight, no matter how
  confident it looks.
- Never promote a rule that contradicts an active rollout policy.
- Rules emitted by this skill are advisory until a human confirms
  them — they must not auto-modify Brain prompts.
- Do not write directly to `HermesMemoryStore` — return the
  prune/promote plan; the caller owns the write.
- This skill runs asynchronously and should never be on the
  critical path of a live verdict.
