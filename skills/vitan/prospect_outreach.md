# Skill — Vitan Prospect Outreach

**Namespace:** `vitan`
**Intended callers:** `vitan:business-builder`, `vitan:outreach-coordinator`.

## When to use

When an agent is asked to turn a prospect profile into an outreach
strategy — i.e. what to say, which projects to showcase, and which
channel to use.

## Trigger conditions

- A contact profile is present in the message (name, company, role,
  location, sector).
- The agent is asking for a tailored approach, not a generic email.

## Process

1. **Classify the prospect** — residential / commercial /
   institutional / mixed-use. If the profile does not specify, ask
   for clarification; never guess.
2. **Match to service lines** — building design, interior design,
   town planning, landscape design, construction oversight. Pick 1-2
   primary, 1 secondary.
3. **Find evidence projects** — relevant past Vitan projects from
   the `branded_content_utils.py` catalog. If no matching projects
   exist, say so; do not fabricate project names or details.
4. **Choose a channel** — email is the default; suggest phone/in-
   person only when the prospect profile justifies it (e.g. local
   Ahmedabad contact with warm intro).
5. **Draft the hook** — one sentence connecting the prospect's stated
   need to a specific Vitan strength, citing at least one evidence
   project.
6. **Hand off** — return the strategy in a format the Outreach
   Coordinator can execute: `{channel, subject_line, hook, evidence,
   call_to_action}`.

## Output format

```
Classification: <segment>
Primary service lines: <a, b>
Secondary service: <c>
Evidence projects: <list or "none in catalog">
Channel: <email | phone | in-person>
Subject line: <max 60 chars>
Hook: <one sentence>
Call to action: <clear, single next step>
Open questions: <if any>
```

## Rules

- Do NOT invent projects, clients, or budgets.
- Do NOT mix in Chanakya-Bot or trading context.
- If a fact is not in memory or the repo, explicitly say "unknown".
- Always offer a "call to action" that is a specific next step, not
  "get in touch".
