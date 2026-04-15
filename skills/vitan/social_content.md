# Skill — Vitan Social Media Content

**Namespace:** `vitan`
**Intended callers:** `vitan:brand-storyteller`, `vitan:digital-presence`.

## When to use

When producing posts for LinkedIn, Facebook, Instagram, or X that
follow Vitan's documented content strategy.

## Strategy mix (from SOCIAL_STRATEGY.md)

| Bucket               | Share | Intent                                         |
|----------------------|-------|-----------------------------------------------|
| Project posts        | 35%   | Showcase completed or in-progress work         |
| Founder perspective  | 25%   | Jagrut's voice: philosophy, lessons, opinion   |
| Process insights     | 20%   | How Vitan works: craft, methodology, sketches  |
| Capabilities         | 15%   | Service-line highlights                        |
| Market commentary    | 5%    | Gujarat / India architecture trends            |

## Process

1. **Check the current mix** — if recent posts (per memory of prior
   runs) have over-indexed on one bucket, pick a bucket that is
   under-represented.
2. **Pick the platform** and respect its constraints:
   - LinkedIn: long form OK (250-500 words), professional tone.
   - Instagram: visual-led, caption supports the photo, hashtags.
   - Facebook: mid-length, slightly less formal than LinkedIn.
   - X: tight (<= 280 chars), link or image.
3. **Draft** using the relevant bucket's voice:
   - Project post → headline + photo reference + outcome.
   - Founder perspective → first-person, specific, no aphorisms.
   - Process insight → concrete craft detail; no generic "attention
     to detail".
   - Capability → service-line framing tied to a recent project.
   - Market commentary → cite a real data point or event.
4. **Add CTA** only when it fits — do not force CTAs onto founder-
   perspective or market-commentary posts.
5. **Log the bucket used** in the output so future runs can balance
   the mix.

## Output format

```
Platform: <linkedin | instagram | facebook | x>
Bucket: <project | founder | process | capability | market>
Caption / post body:
<text>
Hashtags: <list or "none">
Asset reference: <photo id or "needs photo">
CTA: <text or "none">
Rationale: <one line — why this bucket, this platform, this week>
```

## Rules

- Never invent client names, project details, or metrics.
- Do not post about Chanakya-Bot, stock picks, or trading.
- Watch out for repetition — if memory shows a similar angle in the
  last 7 posts, pick a different one.
- Defer to the `project_showcase` skill when the post is a
  project-led piece.
