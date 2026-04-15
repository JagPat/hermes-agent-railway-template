# Vitan — Paperclip Agent Ecosystem

The Vitan namespace is driven by seven Paperclip agents running in the
VITA org on `paperclip.vitan.in`. Each agent has a heartbeat schedule,
wakes periodically, checks assigned issues in Paperclip's ticketing
system, and executes work. Currently all agents use the
`Claude (local)` adapter with `Claude Haiku 4.5` while the Paperclip
HTTP adapter that will route them through Hermes is still marked
"Coming soon".

## Agents and their sessions

| Paperclip agent           | Hermes session                  | Role                                                           |
|---------------------------|---------------------------------|----------------------------------------------------------------|
| Founding Engineer         | `vitan:founding-engineer`       | Technical implementation, codebase quality, automation         |
| Business Builder          | `vitan:business-builder`        | Prospect scanning, market intelligence, outreach strategy      |
| Principle Architect       | `vitan:principle-architect`     | System design, frameworks, best practices research             |
| HR                        | `vitan:hr`                      | Internal processes, team coordination                          |
| Brand Storyteller         | `vitan:brand-storyteller`       | Marketing narrative, content creation                          |
| Digital Presence Manager  | `vitan:digital-presence`        | Social media, web presence                                     |
| Outreach Coordinator      | `vitan:outreach-coordinator`    | Client outreach, partnerships                                  |

## Collaboration patterns

- Business Builder feeds qualified prospects to Outreach Coordinator.
- Brand Storyteller and Digital Presence Manager co-own content — the
  storyteller drafts narrative, the presence manager handles
  distribution and scheduling.
- Principle Architect is the technical-quality gate that Founding
  Engineer's work flows through.
- HR is the internal-operations anchor and should never be asked to
  touch prospect-facing artifacts.

## Phase 2 blocker (do not try to work around)

Paperclip's HTTP adapter is still "Coming soon", so agents cannot yet
route through `hermes.vitan.in/paperclip/invoke` for shared memory.
Agents stay on `Claude (local)` until the adapter ships.
`hermes_local` is NOT a workaround — it runs per-agent isolated
instances without shared memory.

## First-principles rules

1. Treat each agent as a co-worker with long-running context — they
   need Hermes to remember what they were doing last heartbeat.
2. Never collapse multiple agents into one "super-agent" prompt. Each
   has a distinct session for a reason.
3. When the HTTP adapter ships, existing `vitan:*` sessions should
   continue to exist; they become the persistent memory backing the
   adapter calls.
