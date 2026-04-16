#!/bin/bash
set -e

mkdir -p /data/.hermes/sessions
mkdir -p /data/.hermes/skills
mkdir -p /data/.hermes/workspace
mkdir -p /data/.hermes/pairing
mkdir -p /data/.hermes/memory

# ── Seed memory + skills from the image ──────────────────────────────
# This instance is dedicated to Chanakya-Bot (trading platform).
# Files under /app/memory/ and /app/skills/ are shipped in the container.
# On first boot (or when a file is missing) they are copied into the
# persistent /data volume WITHOUT overwriting anything already there —
# Hermes accumulates learned context on top of the seed and we must not
# clobber it on redeploys.
for src in /app/memory/*.md; do
  [ -e "$src" ] || continue
  dst="/data/.hermes/memory/$(basename "$src")"
  if [ ! -e "$dst" ]; then
    cp "$src" "$dst"
    echo "[start.sh] Seeded memory: $dst"
  fi
done
for src in /app/skills/*.md; do
  [ -e "$src" ] || continue
  dst="/data/.hermes/skills/$(basename "$src")"
  if [ ! -e "$dst" ]; then
    cp "$src" "$dst"
    echo "[start.sh] Seeded skill: $dst"
  fi
done

# ── Clean stale namespace subdirs from Phase 3 v1 ────────────────────
# Phase 3 originally seeded into /data/.hermes/memory/{vitan,chanakya}/
# and /data/.hermes/skills/{vitan,chanakya}/. This instance is now
# Chanakya-only with flat directories. Migrate any Chanakya files that
# were seeded under the old namespace path, then remove old dirs.
for dir in memory skills; do
  old="/data/.hermes/$dir/chanakya"
  if [ -d "$old" ]; then
    for f in "$old"/*.md; do
      [ -e "$f" ] || continue
      target="/data/.hermes/$dir/$(basename "$f")"
      if [ ! -e "$target" ]; then
        mv "$f" "$target"
        echo "[start.sh] Migrated $dir: $f → $target"
      fi
    done
    rm -rf "$old"
    echo "[start.sh] Removed old namespace dir: $old"
  fi
  # Remove vitan namespace dir if present (no longer served by this instance)
  old_vitan="/data/.hermes/$dir/vitan"
  if [ -d "$old_vitan" ]; then
    rm -rf "$old_vitan"
    echo "[start.sh] Removed vitan dir: $old_vitan (not served by this instance)"
  fi
done

# Config for Chanakya trading intelligence gateway
MODEL="${LLM_MODEL:-${HERMES_MODEL:-anthropic/claude-haiku-4-5}}"
cat > /data/.hermes/config.yaml <<EOF
model: $MODEL

platform_toolsets:
  api: [memory, session_search, terminal, file, web]
  gateway: [memory, session_search, terminal, file, web]

skills:
  disabled_all: false
EOF
echo "[start.sh] Created config.yaml: model=$MODEL, tools=memory+session_search+terminal+file+web, skills=enabled"

# Clear old sessions (>7 days) to prevent unbounded growth
find /data/.hermes/sessions -name "*.json" -mtime +7 -delete 2>/dev/null || true

# Start Mission Control dashboard on port 9119
hermes dashboard --host 0.0.0.0 --port 9119 --no-open &
DASHBOARD_PID=$!
echo "[start.sh] Dashboard started on port 9119 (PID: $DASHBOARD_PID)"

exec python /app/server.py
