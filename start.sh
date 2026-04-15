#!/bin/bash
set -e

mkdir -p /data/.hermes/sessions
mkdir -p /data/.hermes/skills
mkdir -p /data/.hermes/workspace
mkdir -p /data/.hermes/pairing
mkdir -p /data/.hermes/memory/vitan
mkdir -p /data/.hermes/memory/chanakya
mkdir -p /data/.hermes/skills/vitan
mkdir -p /data/.hermes/skills/chanakya

# ── Phase 3: seed namespaced memory + skills from the image ──────────
# Files under /app/memory/{vitan,chanakya} and /app/skills/{vitan,chanakya}
# are shipped in the container. On first boot (or when a file is missing)
# they are copied into the persistent /data volume WITHOUT overwriting
# anything that is already there — Hermes accumulates learned context on
# top of the seed and we must not clobber it on redeploys.
for ns in vitan chanakya; do
  if [ -d "/app/memory/$ns" ]; then
    for src in /app/memory/$ns/*.md; do
      [ -e "$src" ] || continue
      dst="/data/.hermes/memory/$ns/$(basename "$src")"
      if [ ! -e "$dst" ]; then
        cp "$src" "$dst"
        echo "[start.sh] Seeded memory: $dst"
      fi
    done
  fi
  if [ -d "/app/skills/$ns" ]; then
    for src in /app/skills/$ns/*.md; do
      [ -e "$src" ] || continue
      dst="/data/.hermes/skills/$ns/$(basename "$src")"
      if [ ! -e "$dst" ]; then
        cp "$src" "$dst"
        echo "[start.sh] Seeded skill: $dst"
      fi
    done
  fi
done

# Config optimized for trading gateway:
# KEEP: memory, session_search (Hermes self-learning across sessions)
# REMOVE: file editing, terminal, code execution, vision, cron (coding assistant tools)
# This preserves Hermes' ability to learn and remember while cutting ~10K tokens
MODEL="${LLM_MODEL:-${HERMES_MODEL:-anthropic/claude-haiku-4-5}}"
cat > /data/.hermes/config.yaml <<EOF
model: $MODEL

# Only include tools that support the self-learning architecture
# memory: persistent memory across sessions (learning)
# session_search: recall past conversations (context)
# Everything else is for interactive coding — not needed for API gateway
platform_toolsets:
  api: [memory, session_search, terminal, file, web]
  gateway: [memory, session_search, terminal, file, web]

# Disable accumulated skills (Chanakya has its own FewShot/Hermes learning)
skills:
  disabled_all: false
EOF
echo "[start.sh] Created config.yaml: model=$MODEL, tools=memory+session_search+terminal+file+web, skills=enabled"

# Clear old sessions (>7 days) to prevent unbounded growth
find /data/.hermes/sessions -name "*.json" -mtime +7 -delete 2>/dev/null || true

exec python /app/server.py
