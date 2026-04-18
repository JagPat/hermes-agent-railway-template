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

# ── Config guard ─────────────────────────────────────────────────────
# Preserve existing /data/.hermes/config.yaml when it contains user
# customizations. The baseline below is ONLY seeded when no full config
# is detected. Markers indicating a full/custom config:
#   fallback_providers | smart_model_routing | auxiliary
# Without this guard, every container recreate (Coolify Restart does
# docker rm -f + rebuild, not docker restart) clobbers the routing
# configuration — we learned this on 2026-04-17 during v0.10.0 upgrade.
if grep -qE '^(fallback_providers|smart_model_routing|auxiliary):' /data/.hermes/config.yaml 2>/dev/null; then
  echo "[start.sh] Preserved existing config.yaml (user-customized markers detected)"
else
cat > /data/.hermes/config.yaml <<EOF
model: $MODEL

platform_toolsets:
  api: [memory, session_search, terminal, file, web]
  gateway: [memory, session_search, terminal, file, web]

skills:
  disabled_all: false
EOF
echo "[start.sh] Seeded baseline config.yaml: model=$MODEL, tools=memory+session_search+terminal+file+web, skills=enabled"
fi

# Clear old sessions (>7 days) to prevent unbounded growth
find /data/.hermes/sessions -name "*.json" -mtime +7 -delete 2>/dev/null || true

# ── Start Mission Control dashboard on port 9119 ────────────────────
# Redirect its stdout/stderr to a log file so we can diagnose silent
# startup failures. The wrapper's /gateway/api/diagnostics endpoint
# reads this log and reports bind state on demand.
DASHBOARD_LOG=/data/.hermes/dashboard.log
: > "$DASHBOARD_LOG"  # truncate on each boot
hermes dashboard --host 0.0.0.0 --port 9119 --no-open >>"$DASHBOARD_LOG" 2>&1 &
DASHBOARD_PID=$!
echo "[start.sh] hermes dashboard launched (PID=$DASHBOARD_PID, log=$DASHBOARD_LOG)"

# Probe port 9119 for up to 30s. Logs the outcome so Coolify shows it.
DASHBOARD_UP=""
for i in $(seq 1 30); do
  if ! kill -0 "$DASHBOARD_PID" 2>/dev/null; then
    echo "[start.sh] Dashboard PID $DASHBOARD_PID exited early (attempt $i). Log tail:"
    tail -n 100 "$DASHBOARD_LOG" 2>/dev/null | sed 's/^/[dashboard] /' || true
    break
  fi
  if (exec 3<>/dev/tcp/127.0.0.1/9119) 2>/dev/null; then
    exec 3>&-
    DASHBOARD_UP="yes"
    echo "[start.sh] Dashboard listening on 127.0.0.1:9119 after ${i}s"
    break
  fi
  sleep 1
done

if [ -z "$DASHBOARD_UP" ]; then
  echo "[start.sh] Dashboard did NOT bind to 127.0.0.1:9119 within 30s. Log tail:"
  tail -n 100 "$DASHBOARD_LOG" 2>/dev/null | sed 's/^/[dashboard] /' || true
fi

exec python /app/server.py
