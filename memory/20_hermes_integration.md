# Chanakya — Existing Hermes Integration

This memory summarises the Chanakya-side integration with Hermes that
is **already built and running**. Skills and prompts must AUGMENT this
pipeline, never replace it.

Source files in `JagPat/chanakya-bot`:

| File                                               | Role                                                                                  |
|----------------------------------------------------|---------------------------------------------------------------------------------------|
| `packages/core/brain/hermesClient.js`              | Gateway client — `chat()`, `recordLearning()`, `getLearnedContext()`                  |
| `packages/core/brain/gateway.js`                   | AI Gateway — routes all providers through Hermes when `HERMES_ENABLED=true`           |
| `packages/core/brain/context/hermesContext.js`     | Context builder — injects history, validated insights, accuracy stats into prompts   |
| `packages/core/brain/learning/hermesFeedback.js`   | Feedback logger — writes decision outcomes to `HermesMemoryStore`, detects drift      |
| `packages/core/brain/memory.js`                    | Memory service — persists learned user principles (Postgres)                          |
| `packages/core/config/modelConfig.js`              | Feature → tier mapping (PRO / FLASH) for 30+ AI features                              |

## Gateway mode

When `HERMES_ENABLED=true` and `HERMES_GATEWAY_URL` is set, the
`AIGateway` constructs a single OpenAI-compatible client that points
at `${HERMES_GATEWAY_URL}/v1`. All providers (`openai`, `anthropic`,
`google`, `hermes`) are backed by this same gateway client, so the
model is changed in one place — on the Hermes gateway.

## Fallback discipline

Direct-provider clients (`_directOpenai`, `_directAnthropic`,
`_directGoogle`) exist only for cross-provider fallback when Hermes is
unreachable or all gateway-routed models fail. They require their own
env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`).
If a key is missing, that fallback is simply skipped — not an error.

Health is tracked on `this._hermesHealth`:

```
{ totalCalls, fallbackCount, consecutiveFallbacks, lastSuccess, lastFallback }
```

## Self-learning loop (already operational)

1. Brain generates a verdict → logged to `AIDecisionLog`.
2. 30-day follow-up validates the outcome (`wasCorrect`,
   `outcomeReturn`).
3. `HermesFeedback` extracts an insight → stored in
   `HermesMemoryStore`.
4. `HermesContextBuilder` injects prior insights into the next
   prompt for the same symbol/regime.
5. Concept-drift detection flags periods when recent accuracy drops
   below the long-run baseline.

## Environment variables (authoritative)

| Var                     | Purpose                                            | Example                          |
|-------------------------|----------------------------------------------------|----------------------------------|
| `HERMES_ENABLED`        | Master switch for gateway mode                     | `true`                           |
| `HERMES_GATEWAY_URL`    | Hermes base URL (alt: `HERMES_BASE_URL`)           | `https://hermes.vitan.in`        |
| `HERMES_API_KEY`        | Bearer token for Hermes API                        | `hermes-jagrut`                  |
| `HERMES_MODEL`          | Override model (auto-discovered if unset)          | (auto)                           |
| `LLM_TIMEOUT_MS`        | Standard request timeout                           | `45000`                          |
| `LLM_HEAVY_TIMEOUT_MS`  | Heavy feature timeout                              | `90000`                          |

Heavy features that get the longer timeout:
`STRATEGY_OPTIMIZATION`, `STRATEGY_ADAPTATION`, `RESEARCH`,
`DEEP_ANALYSIS`.

## Phase 3 sessions (new in this deployment)

Chanakya now sends one of these session identifiers on every call
(`x-hermes-session-id` header or `x-caller-id` friendly alias):

- `chanakya:brain` — main orchestration.
- `chanakya:worker` — background analysis loop.
- `chanakya:central` — OTS / service model queries.
- `chanakya:sage` — user-facing chat.
- `chanakya:optimizer` — dedicated context for `STRATEGY_OPTIMIZATION`.
- `chanakya:analyst` — dedicated context for `DEEP_ANALYSIS`.

Each feature is free to reuse `chanakya:brain` by default or target a
feature-specific session so conversation history does not pollute the
general-purpose brain context.
