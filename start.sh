#!/bin/bash
set -e

mkdir -p /data/.hermes/sessions
mkdir -p /data/.hermes/skills
mkdir -p /data/.hermes/workspace
mkdir -p /data/.hermes/pairing

# Create config.yaml with model + disable all skills for lean system prompt
# Skills inflate the system prompt from ~500 tokens to 12K+ tokens
# For a trading gateway, we don't need general-purpose skills
MODEL="${LLM_MODEL:-${HERMES_MODEL:-anthropic/claude-haiku-4-5}}"
cat > /data/.hermes/config.yaml <<EOF
model: $MODEL
skills:
  disabled:
    - "*"
EOF
echo "[start.sh] Created config.yaml with model=$MODEL, skills disabled for lean prompt"

# Clear accumulated skills to prevent system prompt inflation
# Hermes learns and saves skills over time — each one adds tokens to every request
if [ "${HERMES_CLEAR_SKILLS:-false}" = "true" ]; then
  rm -rf /data/.hermes/skills/*
  echo "[start.sh] Cleared accumulated skills (HERMES_CLEAR_SKILLS=true)"
fi

# Clear old sessions to prevent memory accumulation
find /data/.hermes/sessions -name "*.json" -mtime +7 -delete 2>/dev/null || true
echo "[start.sh] Cleaned sessions older than 7 days"

exec python /app/server.py
