# Skill — Chanakya Risk Calibration

**Namespace:** `chanakya`
**Intended callers:** `chanakya:brain`, `chanakya:optimizer`,
`chanakya:analyst`.

## When to use

When a verdict, trade plan, or strategy mutation needs a calibrated
risk read — cross-referencing stated confidence against the system's
actual historical accuracy.

## Inputs

- `HermesFeedback.getConfidenceCalibration()` — observed accuracy
  bucketed by confidence level.
- `AIDecisionLog` recent window (configurable, default 90 days).
- Current regime classification.
- The candidate action and its stated confidence.

## Process

1. **Bucket the stated confidence** into the same buckets the
   calibration function uses (e.g. 0.5-0.6, 0.6-0.7, …).
2. **Look up observed accuracy** for that bucket in the current
   regime. If there is not enough data for the current regime, fall
   back to the global bucket accuracy and mark the output as
   `thin_sample`.
3. **Compute calibration gap** — stated confidence minus observed
   accuracy.
4. **Flag one of four states**:
   - `well_calibrated` — gap within ±5%.
   - `overconfident` — gap > +5% (stated higher than observed).
   - `underconfident` — gap < -5% (stated lower than observed).
   - `no_signal` — sample too thin to decide.
5. **Adjust the recommendation**:
   - `overconfident` → recommend reducing position size or
     delaying the action.
   - `underconfident` → note that the action could be executed with
     the stated confidence, but still respect hard risk limits.
   - `no_signal` → defer to the risk manager's hard limits; skill
     gives no confidence adjustment.
6. **Never override** `packages/core/risk/index.js` or the kill
   switch — calibration adjusts sizing/confidence, not gates.

## Output format

```json
{
  "stated_confidence": 0.0,
  "observed_accuracy": 0.0,
  "bucket": "0.6-0.7",
  "regime": "...",
  "sample_size": 0,
  "state": "well_calibrated | overconfident | underconfident | no_signal",
  "calibration_gap": 0.0,
  "recommended_adjustment": "...",
  "hard_limits_respected": true
}
```

## Rules

- Always return `hard_limits_respected: true` if the skill did not
  override risk-manager constraints; if it would need to, stop and
  return `state: "no_signal"` with an explanation.
- Never calibrate on less than 10 samples without marking
  `thin_sample`.
- Do not persist calibration outputs into `HermesMemoryStore` —
  they are derived, not primary evidence.
