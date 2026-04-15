# Skill — Vitan Cross-Agent Synthesis

**Namespace:** `vitan`
**Intended callers:** `vitan:principle-architect`,
`vitan:founding-engineer`, any coordinator role.

## When to use

When the task output depends on work from more than one Paperclip
agent and those outputs need to be reconciled into a single coherent
deliverable.

## Typical triggers

- A prospect-facing document that combines Business Builder's
  qualification with Brand Storyteller's narrative and a project
  showcase.
- A process doc blending HR's workflow notes with Founding
  Engineer's automation pass.
- A social campaign built from Digital Presence Manager's calendar
  plus Brand Storyteller's narrative and project assets.

## Process

1. **Identify contributors** — which agents produced source material
   for this task. Name them explicitly in the output.
2. **Load each agent's relevant session memory** — `vitan:business-
   builder`, `vitan:brand-storyteller`, etc. If a session has no
   prior context on this task, say so instead of confabulating.
3. **Reconcile conflicts** — if two agents disagree (e.g. Business
   Builder's "residential prospect" vs Brand Storyteller's
   "commercial narrative"), flag the conflict rather than silently
   picking a side. Return the conflict with a recommended
   resolution.
4. **Deduplicate** — remove facts that appear in multiple inputs; a
   fact need not appear twice.
5. **Assemble** in the order: (a) factual foundation, (b)
   narrative, (c) call to action.
6. **Credit sources** — the output should make it clear which agent
   contributed which piece, so the next person editing it knows
   who to go back to.

## Output format

```
Contributors: <list of vitan: sessions>
Conflicts: <list or "none">
Deliverable:
  Facts:
    - <bullet>
  Narrative:
    <paragraphs>
  Call to action:
    <text>
Source map:
  - <fact/section> ← <contributing agent>
Open follow-ups: <list or "none">
```

## Rules

- Never smooth over a conflict by guessing which agent is right —
  surface it.
- Never pull from `chanakya:*` sessions.
- Treat HR outputs as internal-only unless the task is explicitly
  HR-facing.
- If one contributing agent's input is stale (older than the
  task's own context window), flag it.
