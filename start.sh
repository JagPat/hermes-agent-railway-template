#!/bin/bash
set -e

mkdir -p /data/.hermes/sessions
mkdir -p /data/.hermes/skills
mkdir -p /data/.hermes/workspace
mkdir -p /data/.hermes/pairing

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
