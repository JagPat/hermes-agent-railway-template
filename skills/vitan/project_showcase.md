# Skill — Vitan Project Showcase

**Namespace:** `vitan`
**Intended callers:** `vitan:brand-storyteller`, `vitan:digital-presence`,
`vitan:outreach-coordinator`.

## When to use

When an agent needs to turn a Vitan project into a compelling
description for a pitch, PDF, email, or social post.

## Trigger conditions

- A specific project (or list of projects) is being described.
- The consumer is prospect-facing or public (not internal).

## Process

1. **Pull project facts** from the Vitan-BrandBuilding project
   catalog (`branded_content_utils.py`). Facts allowed in output:
   project name, location, typology, built-up area, client segment,
   year, photography availability.
2. **Pick the narrative angle** based on consumer intent:
   - Pitch → outcome / problem solved.
   - Social post → process / craftsmanship moment.
   - PDF → breadth and design philosophy.
3. **Structure the description** in three layers:
   - **Headline** (one line, <= 12 words, no clichés).
   - **Body** (2-4 sentences, concrete, project-centric).
   - **Evidence** (key metrics and photograph references, bulleted).
4. **Match the tone** to the guidance in `SOCIAL_STRATEGY.md`:
   understated, project-centric, photography-led.
5. **Flag missing assets** — if the project has no photographs or
   the catalog lacks a field you need, say so explicitly instead of
   guessing.

## Output format

```
Headline: <one line>
Body: <2-4 sentences>
Evidence:
  - Location: ...
  - Area: ...
  - Typology: ...
  - Client segment: ...
  - Photography: <yes/no; reference ids>
Missing / unknowns: <list or "none">
```

## Rules

- Strictly factual. No invented metrics, awards, or client quotes.
- Never mix Chanakya-Bot trading content.
- If the project is under NDA or confidential, return an abstracted
  version and flag it as such.
- For social posts, honour the SOCIAL_STRATEGY mix: project posts
  (35%), founder perspective (25%), process insights (20%),
  capabilities (15%), market commentary (5%).
