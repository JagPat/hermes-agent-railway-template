# Vitan Architects — Product Overview

**Namespace:** `vitan`
**Audience:** Sessions prefixed `vitan:` (Paperclip agents, direct Vitan
API callers).

## What Vitan Architects is

Vitan Architects is an established architecture and design consultancy
based in Ahmedabad, Gujarat, India. It was founded in the early 1990s
and operates with roughly 30 staff. The firm's practice areas span:

- Building design
- Interior design
- Town planning
- Landscape design
- Construction oversight

The client base is residential and commercial projects across Gujarat.

## Why Hermes exists for Vitan

Jagrut Patel (founder) is building an autonomous agent ecosystem to
scale Vitan's business development, branding, and operational
workflows. Hermes is the central brain those agents share. It
provides:

- **Persistent memory** across agent wakeups, so context survives
  restarts and is accumulated, not rebuilt from scratch each run.
- **Shared skills** so every agent follows the same playbooks.
- **Session isolation** (via the `vitan:` namespace) so Vitan's
  conversational context never bleeds into Chanakya-Bot — the
  personal trading product that shares the same Hermes deployment.

## What this namespace must NEVER do

- Reference Chanakya-Bot trading data, stock verdicts, or broker state.
- Pull from `chanakya:*` sessions or memories.
- Treat Vitan as a software product — it is an architecture firm; the
  AI layer is tooling, not the business itself.

## Memory loading contract

Files under `/data/.hermes/memory/vitan/` are seeded on first boot by
`start.sh`. They are NOT overwritten on subsequent boots, so the Vitan
namespace can accumulate learned context from actual agent runs on top
of this seed.
