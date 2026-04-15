# Skill — Vitan Architecture Brief Analysis

**Namespace:** `vitan`
**Intended callers:** `vitan:principle-architect`,
`vitan:founding-engineer`, `vitan:business-builder`.

## When to use

When a project brief, RFP, or tender document arrives and the agent
needs to assess requirements, estimate scope, identify design
considerations, and flag similar past projects.

## Process

1. **Extract hard requirements**:
   - Site location, plot size, typology.
   - Program / brief summary.
   - Budget (if stated — never guess).
   - Timeline and submission deadline.
   - Regulatory context (local authority, zoning).
2. **Extract soft requirements**:
   - Client aesthetic preferences, if any.
   - Sustainability targets.
   - Cultural / contextual cues (Gujarat-specific language,
     vernacular references).
3. **Identify design considerations**:
   - Climate-appropriate strategies for the site region.
   - Structural and MEP implications of the program.
   - Cost-driving decisions (basements, large spans, facades).
4. **Flag past projects** — search the Vitan project catalog for 2-3
   comparable projects by typology + size. Cite them by name; never
   invent matches.
5. **Estimate scope in service-line terms** — which Vitan service
   lines are needed (building design, interior, landscape, town
   planning, oversight). Do NOT estimate fees.
6. **Risk flags** — anything in the brief that is unusual, under-
   specified, or commercially risky (payment terms, unclear scope,
   aggressive timeline).

## Output format

```
Hard requirements:
  - Location: ...
  - Plot: ...
  - Typology: ...
  - Program: ...
  - Budget: <value or "not stated">
  - Timeline: ...
  - Regulator: ...
Soft requirements: ...
Design considerations:
  - <bullet>
Service lines needed: <list>
Comparable past projects: <list or "none in catalog">
Risk flags: <list or "none">
Recommended next step: <one clear action>
```

## Rules

- Never invent numbers, regulations, or past projects.
- Fees and commercials are out of scope; flag but do not estimate.
- If the brief is incomplete, list the open questions explicitly —
  do not fill gaps with assumptions.
- Do not cross-reference Chanakya-Bot material.
