# Vitan — Business & Market Context

## Geography

- Primary market: **Gujarat, India** (residential and commercial).
- Home base: **Ahmedabad**.
- Operates locally, not remotely — this affects site visits,
  construction oversight, and client relationships.

## Service lines

- **Building design** — residential and commercial projects.
- **Interior design** — works alongside building design for turnkey
  engagements.
- **Town planning** — larger-scale urban projects.
- **Landscape design** — commonly paired with building design.
- **Construction oversight** — differentiator versus
  purely-advisory practices.

## Business development workflow (as documented in Vitan-BrandBuilding)

This is the workflow the Paperclip agents automate. Exact details live
in the `JagPat/Vitan-BrandBuilding` repository; the Hermes namespace
should not duplicate that repo's source of truth, only reason about it.

- **Prospect qualification** — Business Builder identifies candidate
  clients and enriches them with sector/geography/budget signals.
- **Branded email generation** — `generate_branded_email.py` produces
  personalised HTML emails matching relevant projects to prospects.
- **Branded PDF generation** — `generate_branded_pdf.py` produces
  pitch PDFs with project details.
- **Social media content** — `SOCIAL_STRATEGY.md` defines LinkedIn,
  Facebook, Instagram, X mix: project posts (35%), founder perspective
  (25%), process insights (20%), capabilities (15%), market
  commentary (5%).
- **WorkDrive sync** — Zoho WorkDrive scripts keep generated artifacts
  in shared storage.

## What Hermes should treat as authoritative

- Actual project catalog, contact database, logo/image assets, and
  content templates all live in the Vitan-BrandBuilding repo.
- The `branded_content_utils.py` module is the canonical data
  accessor; agents should ask that module rather than inventing
  project metadata.
- If any prospect or project detail isn't in the repo, the answer is
  "I don't know", NOT a plausible-sounding fabrication.

## What Hermes should never assume

- Client names, deal sizes, or project budgets unless a session
  explicitly records them.
- Competitor positioning — Vitan's competitive landscape is not
  documented in this memory space.
- Pricing or fee structures.

## Tone guidance for generated content

- Professional, understated, project-centric.
- Photographs and project evidence lead the narrative; copy supports
  them.
- Gujarat market cues (local references, regional sensibilities) are
  appropriate when the prospect is local.
