#!/bin/bash
set -e

mkdir -p /data/.hermes/sessions
mkdir -p /data/.hermes/skills
mkdir -p /data/.hermes/workspace
mkdir -p /data/.hermes/pairing

# Create config.yaml optimized for trading gateway use case:
# - Minimal tools (no file editing, terminal, code execution)
# - No skills (Chanakya has its own learning system)
# - Lean system prompt (~500 tokens instead of 12K)
MODEL="${LLM_MODEL:-${HERMES_MODEL:-anthropic/claude-haiku-4-5}}"
cat > /data/.hermes/config.yaml <<EOF
model: $MODEL

# Disable all tools for API/gateway mode — Chanakya only uses chat completions
# Each tool definition adds ~500-800 tokens to the system prompt
# 16 tools = ~12,000 tokens of overhead on every single call
platform_toolsets:
  api: []
  gateway: []
  cli: []

# Disable all skills — Chanakya has its own FewShot/Hermes learning system
skills:
  disabled_all: true

# Lean agent — no tool enforcement, no skill guidance
agent:
  tool_use_enforcement: false
EOF
echo "[start.sh] Created config.yaml: model=$MODEL, tools disabled, skills disabled"

# Clear accumulated skills
rm -rf /data/.hermes/skills/*
echo "[start.sh] Cleared accumulated skills"

# Clear old sessions (>7 days)
find /data/.hermes/sessions -name "*.json" -mtime +7 -delete 2>/dev/null || true

exec python /app/server.py
